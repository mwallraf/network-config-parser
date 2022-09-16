import logging
import json
import re
import sys, traceback


# logger = logging.getLogger(__name__)

####   #logger.setLevel(logging.DEBUG)
####   logger.setLevel(logging.CRITICAL)
####   screenformatter = logging.Formatter('%(asctime)s - %(name)s [%(lineno)d] - %(levelname)s - %(message)s')
####   logprinter = logging.StreamHandler()
####   logprinter.setFormatter(screenformatter)
####   logger.addHandler(logprinter)

UNKNOWN = "-unknown-"
NONE = "-none-"


class ParserCollection(object):
    """
    This class defines a list of parsed objects.
    Procedures can be defined to link the objects together
    """

    DEBUG = False

    def __init__(self, **kwargs):
        ParserCollection.DEBUG = kwargs.get("debug", False)
        # if ParserCollection.DEBUG:
        #    logger.setLevel(logging.DEBUG)

        self.logger = logging.getLogger(__name__)

        self.parserlist = []
        self.logicalringinfo = None
        self.virtualringinfo = None
        self.switchportinfo = None
        self.vlaninfo = None
        self.serviceinfo = None
        self.vringnames = None  # unique virtual-ring names
        self.lringnames = None  # unique logical-ring names
        self.coldelim = "_"  # used when joining fields inside a column

    def append(self, p):
        self.parserlist.append(p)

    def test(self):
        print(self)

    def object_by_hostname(self, hostname):
        """
        Returns the host object based on the hostname
        """
        for h in self.parserlist:
            if h.model.host.hostname == hostname:
                return h

        return None

    def _is_class(self, o):
        """
        Checks if a variable is a Class object (Class)
        Returns True if it is
                False if it's not
        """
        return True if hasattr(o, "__dict__") else False

    def _linkcollection_lldp(self):
        # link devices together based on LLDP, find the neighbor and neighbor port object reference
        ## TODO: add aggregation ports
        for s in self.parserlist:
            # for each lldpneighbor id, see if we can find a matching chassis
            for n in s.model.lldpneighbors:
                # print("n = {}".format(n))
                # print("n.nbr = {}".format(n.nbr))
                # b = [ x.model.host.chassisid for x in self.parserlist ]
                # print("b = {}".format(b))
                nbr = next(
                    iter(
                        list(
                            filter(
                                lambda x: str(x.model.host.chassisid).upper()
                                == str(n.nbr),
                                self.parserlist,
                            )
                        )
                    ),
                    None,
                )
                # print("nbr = {}".format(nbr))
                if nbr:
                    # print("nbr has been set for {} - {} - {}".format(s.model.host.hostname, n.nbr, nbr))
                    n.nbr = nbr
                    nbrport = next(
                        iter(
                            list(
                                filter(
                                    lambda x: str(x) == str(n.nbrPort),
                                    nbr.model.switchports,
                                )
                            )
                        ),
                        None,
                    )
                    n.nbrPort = nbrport

    def linkCollection(self):
        """
        This function tries to replace data with a link towards the object of another device.
        For example: if a port has a vlan id and the same vlan object exists, then the
           port vlan id will be rapleced by the vlan object reference.

        Parserlist = list of all parsed devices (ex. list of parsed SDS configurations)
        """
        self._linkcollection_lldp()

        ## # Link devices together based on logical-rings
        ## def _walk_the_ring(port, startchassis, ringid, direction="west"):
        ##     """
        ##     Internal method to go over a ring hop by hop and determine the ring members + ring status
        ##     """
        ##     keepwalking = True
        ##     #rc = { 'complete': False, 'neighbor': None }
        ##     # continue if the westport is a reference to an object
        ##     while keepwalking and hasattr(port, '__dict__'):
        ##         rc = { 'complete': False, 'neighbor': None }
        ##         if port and port.lldpnbr:
        ##             # get the neighbor object from the LLDP info inside the local port
        ##             nbr = port.lldpnbr.nbr
        ##             #print nbr
        ##             #print westport
        ##             if not hasattr(nbr, '__dict__'):
        ##                 # no neighbor object found
        ##                 keepwalking = False
        ##             elif str(nbr.model.host.chassisid) == str(startchassis):
        ##                 # neighbor is the same as starting device so the ring should be complete
        ##                 rc['complete'] = True
        ##                 keepwalking = False
        ##                 yield rc
        ##             else:
        ##                 # find the neighbor port based on ringid + LLDP information stored in the port
        ##                 rc['neighbor'] = nbr
        ##                 nbrring = next(iter(list(filter(lambda x: (x.type == 'logical-ring') and (x.id == ringid), nbr.model.rings))), None)
        ##                 if direction == "east":
        ##                     port = nbrring.eastport if (nbrring and nbrring.eastport) else None
        ##                 else:
        ##                     port = nbrring.westport if (nbrring and nbrring.westport) else None
        ##                 yield rc
        ##         else:
        ##             keepwalking = False

        ## def _start_walking(r, s, direction="west"):
        ##     #westport = r.westport or None ## should contain reference to local westport
        ##     #eastport = r.eastport or None ## should contain reference to local eastport
        ##     startport = r.eastport or None if direction == 'east' else r.westport or None
        ##     startchassis = s.model.host.chassisid
        ##     ringmembers = []
        ##     ringstatus = "unknown"
        ##     # find the ring neighbors hop by hop
        ##     for rc in _walk_the_ring(startport, startchassis, r.id, direction=direction):
        ##         if rc['neighbor'] in ringmembers:
        ##             logger.error("INFINITE LOOP DETECTED, {} ALREADY PROCESSED - BREAKING OUT OF IT".format(rc['neighbor']))
        ##             break
        ##         if rc and rc['neighbor']:
        ##             ringmembers.append(rc['neighbor'])
        ##         if rc and rc['complete']:
        ##             ringstatus = "closed"
        ##     #print members
        ##     if (len(ringmembers) > 0 and ringstatus == "unknown") or (len(ringmembers) == 0):
        ##         ringstatus = "open"
        ##     return { "status": ringstatus, "members": ringmembers }

        ## # Determine ring status (open/closed) and ring members
        ## # TODO: for open rings also process eastbound !!
        ## for s in self.parserlist:
        ##     rings = [ x for x in s.model.rings if x.type == 'logical-ring' ]
        ##     for r in rings:
        ##         #print "ring {} on chassis {}".format(str(r), s.model.host.hostname)
        ##         # travel WEST
        ##         r.ringstatus = "unknown"
        ##         ringwest = _start_walking(r, s, direction="west")
        ##         ringeast = (_start_walking(r, s, direction="east"))
        ##         ringeast["members"].reverse()
        ##         # in case the ring is open we should find the path in both directions
        ##         if ringwest["status"] == ringeast["status"] == "closed":
        ##             r.ringstatus = "closed"
        ##         elif ringeast["status"] == "open" or ringeast["status"] == "open":
        ##             r.ringstatus = "open"
        ##         ringmembers = ringeast["members"] + [s] + ringwest["members"]
        ##         #if len(set(ringmembers)) == 1:
        ##         #    r.ringstatus = "open"
        ##         r.ringmembers = list(set(ringmembers))
        ##         #r.ringmembers = sorted(set(ringmembers), key=lambda m: m.model.host.hostname)
        ##         logger.debug("HOST {} _ RING {} _ {} _ MEMBERS: {}".format(s.model.host.hostname, r.name, r.ringstatus, ",".join([ a.model.host.hostname for a in r.ringmembers ] )))

    def get_ring_status_code(self, ring):
        """
        Returns the general status of a ring depending on the number of errors and
        severity of the error
        0 = OK
        1-9 = OK - WARNINGS
        10-x = NOT OK
        min severity = 10

        # weight: INFO, WARN, ERROR, CRITICAL
        #         0-4, 5-9, 10-14, 15-19

        """
        categories = {
            "OK": range(0, 1),
            "OK - WARNINGS": range(1, 10),
            "NOT OK": range(10, 20),
        }
        mapping = {}

        for cat in categories:
            for sev in categories[cat]:
                mapping[str(sev)] = cat

        highest_weight = 0
        errors = ring["errors_cat"]
        for category in errors:
            if errors[category].get("count", 0) > 0:
                new_weight = errors[category].get("weight", 0)
                highest_weight = (
                    new_weight
                    if new_weight > highest_weight
                    else highest_weight
                )

        status_code = (
            "OK" if highest_weight is None else mapping[str(highest_weight)]
        )
        # print("Severity: {}".format(severity))

        return status_code

    def get_severity_from_errors(self, errors):
        """
        Returns the maximum error category as a single "severity" value
        Severity:
            weight: INFO, WARN, ERROR, CRITICAL
                     0-4, 5-9, 10-14, 15-19
        """
        categories = {
            "INFO": range(0, 5),
            "WARN": range(5, 10),
            "ERROR": range(10, 15),
            "CRITICAL": range(15, 20),
        }
        mapping = {}

        for cat in categories:
            for sev in categories[cat]:
                mapping[str(sev)] = cat

        highest_weight = 0
        for category in errors:
            if errors[category].get("count", 0) > 0:
                new_weight = errors[category].get("weight", 0)
                highest_weight = (
                    new_weight
                    if new_weight > highest_weight
                    else highest_weight
                )

        severity = (
            "OK" if highest_weight is None else mapping[str(highest_weight)]
        )
        # print("Severity: {}".format(severity))

        return severity

    def get_netjson_lldp(self):
        """
        Returns a netjson representation for all nodes and links.
        Unique key = chassis-id
        {
            "nodes": [ { "id": "00387-SDS39-002","properties": { "Management IP": "10.8.91.98" } },
                    ],
            "links": [ { "source": "", "target": "", "properties": {} }
                    ]
        }
        """
        nodes = []
        links = []
        for p in self.parserlist:
            pjson = json.loads(
                p.model.get_netjson_lldp() or '{ "nodes": [], "links": [] }'
            )
            # print("pjson = {}".format(pjson))
            for node in pjson["nodes"]:
                # print("node = {}".format(node))
                n = next(
                    iter(
                        list(
                            filter(
                                lambda x: str(x["id"]) == str(node["id"]),
                                nodes,
                            )
                        )
                    ),
                    None,
                )
                if not n:
                    nodes.append(node)
            for link in pjson["links"]:
                n = next(
                    iter(
                        list(
                            filter(
                                lambda x: "{}-{}".format(
                                    x["source"], x["target"]
                                )
                                == "{}-{}".format(
                                    link["source"], link["target"]
                                ),
                                links,
                            )
                        )
                    ),
                    None,
                )
                if not n:
                    links.append(link)
        j = {"nodes": nodes, "links": links}
        return json.dumps(j, indent=4, separators=(",", ": "))

    def get_switchport_status(self, refresh=False):
        """
        Returns a list of interfaces and the configured + operational status
        {
            "hostname": "",
            "ports': [
                { 'port': '', 'rstp': '', 'mstp': '', 'lldp': '', 'lldpnbr': '',
                  'descr': '', 'operstate': '', 'adminstate': '', 'adminspeedduplex': '',
                  'operspeedduplex': '', 'linkstateduration': '', 'xsvrstatus': '',
                  'autoneg': '', 'stormcontrol': '', 'vlans': [], 'mtu': '', 'egress-policy': ''
                }
            ]
        }

        Error checking:
            - VLAN 127 should not be present except for SAS87
            - VLAN 1 should not be present on admin UP interfaces
            - MTU size should be 9100 on UNI and 9216 on NNI on admin UP interfaces
            - egress policy should match port speed
            - duplex should not be half duplex
        """

        # if the result is known and refresh is not needed then just return the restul
        if self.switchportinfo and not refresh:
            return self.switchportinfo

        nodes = []

        # weight: INFO, WARN, ERROR, CRITICAL
        #         0-4, 5-9, 10-14, 15-19
        def create_error_categories():
            return {
                "vlan_issues": {"count": 0, "weight": 5},
                "mtu_issues": {"count": 0, "weight": 5},
                "speed_issues": {"count": 0, "weight": 5},
                "duplex_issues": {"count": 0, "weight": 5},
            }

        # minimum list of fields, if it does not exist then add NONE
        min_rqd_fields = [
            "name",
            "adminstate",
            "adminspeedduplex",
            "operstate",
            "operspeedduplex",
            "autoneg",
            "linkstateduration",
            "description",
            "lldp",
            "rstp",
            "stormcontrol",
            "xsvrstatus",
            "lldpnbr",
            "mtu",
            "type",
            "ports",
            "_vlans",
            "speedcapability",
            "vplsporttype",
            "egressqueue",
            "egressshaper",
        ]

        def create_record(hostname, port):
            """
            Make sure each object has the minimum required fields
            to make it easier for reporting later
            """
            p = {}
            for f in min_rqd_fields:
                p[f] = getattr(port, f, None)
            p["errors"] = []
            p["errors_cat"] = create_error_categories()

            ## replace the objects by values
            try:
                p["lldpnbr"] = str((p["lldpnbr"].nbr.model.host.hostname))
            except:
                if self._is_class(p["lldpnbr"]):
                    p["lldpnbr"] = str(p["lldpnbr"].nbr)
                else:
                    p["lldpnbr"] = str(p["lldpnbr"])
            p["_vlans"] = [
                str(v.vlan) if self._is_class(v) else str(v)
                for v in p["_vlans"]
            ]

            ## check for errors
            # VLAN 127 should not be present except for SAS87
            if "SAS87" not in hostname and "127" in p["_vlans"]:
                p["errors"].append(
                    "{} port {} - Vlan 127 should not be configured on this port".format(
                        hostname, p["name"]
                    )
                )
                p["errors_cat"]["vlan_issues"]["count"] += 1
            # VLAN 1 should not be configured on admin UP interfaces
            if p["adminstate"] == "enabled" and "1" in p["_vlans"]:
                p["errors"].append(
                    "{} port {} (admin state = {}) - Vlan 1 should not be configured on this port".format(
                        hostname, p["name"], p["adminstate"]
                    )
                )
                p["errors_cat"]["vlan_issues"]["count"] += 1
            # MTU size 9100 for NNI and 9216 for UNI
            if (
                p["adminstate"] == "enabled"
                and p["vplsporttype"] == "NNI"
                and p["mtu"] != "9100"
            ):
                p["errors"].append(
                    "{} NNI port {} - MTU size is {} but should be 9100".format(
                        hostname, p["name"], p["mtu"]
                    )
                )
                p["errors_cat"]["mtu_issues"]["count"] += 1
            if (
                p["adminstate"] == "enabled"
                and p["vplsporttype"] == "UNI"
                and p["mtu"] != "9216"
            ):
                p["errors"].append(
                    "{} UNI port {} - MTU size is {} but should be 9216".format(
                        hostname, p["name"], p["mtu"]
                    )
                )
                p["errors_cat"]["mtu_issues"]["count"] += 1
            # duplex issues
            if (
                p["operspeedduplex"]
                and p["adminstate"] == "enabled"
                and "HD" in p["operspeedduplex"]
            ):
                p["errors"].append(
                    "{} port {} - duplex issues {}".format(
                        hostname, p["name"], p["operspeedduplex"]
                    )
                )
                p["errors_cat"]["duplex_issues"]["count"] += 1
            # speed issues
            if (
                p["operspeedduplex"]
                and p["adminstate"] == "enabled"
                and p["egressshaper"]
            ):
                m = re.match("(?P<OPERSPEED>[0-9]+).*", p["operspeedduplex"])
                if m:
                    if m.groupdict().get("OPERSPEED", 0) != p["egressshaper"]:
                        p["errors"].append(
                            "{} port {} - egress shaper mismatch {} with operational speed {}".format(
                                hostname,
                                p["name"],
                                p["egressshaper"],
                                p["operspeedduplex"],
                            )
                        )
                        p["errors_cat"]["speed_issues"]["count"] += 1
            return p

        for p in self.parserlist:
            # pjson = p.model.get_switchport_status()
            # node = json.loads(pjson)
            # node = p.model.get_switchport_status()
            hostname = (
                p.model.host.hostname or p.model.host.chassisid or UNKNOWN
            )
            node = {"hostname": hostname, "ports": []}
            if node.get("hostname", None) and p.model.switchports:
                ports = []
                for p in p.model.switchports:
                    ports.append(create_record(node["hostname"], p))
                node["ports"] = ports
            nodes.append(node)

        self.switchportinfo = {"nodes": nodes}

        # flat json reporting for easy import in splunk
        json_output = []
        for node in self.switchportinfo["nodes"]:
            json_output.append(
                json.dumps(node, indent=4, separators=(",", ": "))
            )
        return "\n".join(json_output)

        # print(nodes)
        # self.switchportinfo = { 'nodes': nodes }
        # return json.dumps(self.switchportinfo, indent=4, separators=(',', ': '))

    def _logical_ring_status(self, logicalring):
        """
        Check each member of the logical ring and ensure there are:
        - 2 active ports
        - each port has an LLDP neighbor
        - the combination of all LLDP neighbors should be exactly the same as the combination of the ringmembers
        - check unique ring naming, 1 name per RID
        """
        ## check if there are 2 active ports
        lldp_members = []
        ring_members = sorted(
            list(
                set(
                    [
                        x.model.host.hostname if self._is_class(x) else x
                        for x in logicalring["ringmembers"]
                    ]
                )
            ),
            key=lambda x: x,
        )

        for rmember in logicalring["ringmembers"]:
            self.logger.debug("ringmember: {}".format(rmember))

            if not self._is_class(rmember):
                logicalring["errors"].append(
                    "ring member {} is not an object".format(rmember)
                )
                logicalring["errors_cat"]["lldp_issues"]["count"] += 1
                continue

            mhostname = rmember.model.host.hostname
            # find the logical ring for this member
            lr = next(
                iter(
                    list(
                        filter(
                            lambda x: (x.name == logicalring["name"])
                            and (x.type == "logical-ring"),
                            rmember.model.rings,
                        )
                    )
                ),
                None,
            )
            self.logger.debug(
                "logical ring found for the ring member: {}".format(lr)
            )

            if not (lr.eastport and lr.westport):
                logicalring["errors"].append(
                    "{} - {}: missing logicalring port".format(
                        mhostname, lr.name
                    )
                )
                logicalring["errors_cat"]["logical_ring_missing"]["count"] += 1
                logicalring["errors_cat"]["ring_open_issues"]["count"] += 1
                continue
            for port in [lr.eastport, lr.westport]:
                self.logger.debug("checking east-west port: '{}'".format(port))

                if not self._is_class(port):
                    logicalring["errors"].append(
                        "{} - {} - {}: logicalring ports are unknown".format(
                            mhostname, lr.name, port.name
                        )
                    )
                    logicalring["errors_cat"]["port_issues"]["count"] += 1
                    logicalring["errors_cat"]["ring_open_issues"]["count"] += 1
                    continue

                lldpnbr = port.lldpnbr
                if not self._is_class(lldpnbr):
                    logicalring["errors"].append(
                        "{} - {} - {} - {}: lldp neighbor is not an object".format(
                            mhostname, lr.name, port.name, lldpnbr
                        )
                    )
                    logicalring["errors_cat"]["lldp_issues"]["count"] += 1
                    logicalring["errors_cat"]["ring_open_issues"]["count"] += 1
                    self.logger.debug(
                        "LLDP ISSUE - lldp neighbor is not an object - {}".format(
                            lldpnbr
                        )
                    )
                    continue

                lldpnbr = port.lldpnbr.nbr
                if not self._is_class(lldpnbr):
                    logicalring["errors"].append(
                        "{} - {} - {} - {}: lldp neighbor is not an object".format(
                            mhostname, lr.name, port.name, lldpnbr
                        )
                    )
                    logicalring["errors_cat"]["lldp_issues"]["count"] += 1
                    logicalring["errors_cat"]["ring_open_issues"]["count"] += 1
                    self.logger.debug(
                        "LLDP ISSUE - lldp neighbor is not an object - {}".format(
                            lldpnbr
                        )
                    )
                    continue

                lldpnbr = lldpnbr.model.host.hostname or None
                if lldpnbr:
                    lldp_members.append(lldpnbr)
                else:
                    logicalring["errors"].append(
                        "{} - {} - {}: no LLDP neighbor found for port".format(
                            mhostname, lr.name, port.name
                        )
                    )
                    logicalring["errors_cat"]["lldp_issues"]["count"] += 1
                    logicalring["errors_cat"]["ring_open_issues"]["count"] += 1
                    continue

        ## check if the neighbors are the same as the ringmembers
        lldp_members = sorted(list(set(lldp_members)), key=lambda x: x)
        if not set(lldp_members) == set(ring_members):
            logicalring["errors"].append(
                "LLDP neighborships [{}] do not match ring members [{}]".format(
                    ", ".join(lldp_members), ", ".join(ring_members)
                )
            )
            logicalring["errors_cat"]["lldp_issues"]["count"] += 1
            logicalring["errors_cat"]["ring_open_issues"]["count"] += 1

        # check unique ring name, 1 LR name per RID
        # if logicalring['name'] and len(set(lr_rid[logicalring['id']])) > 1:
        #    logicalring['errors'].append("{} - multiple LR names with the same RID {}: {}".format(logicalring['name'], logicalring['id'], ",".join(set(lr_rid[logicalring['id']]))))
        #    logicalring['errors_cat']['ring_naming_issues']['count'] += 1

        ## set the ring status (exclude naming issues)
        if logicalring["errors_cat"]["ring_open_issues"]["count"] > 0:
            logicalring["status"] = "open"
        else:
            logicalring["status"] = "closed"

    def get_logical_ring_info(self, refresh=False):
        """
        Returns information per unique logical ring in JSON format
        Unique key = ringname-ringid
            - ringmembers
            - ring status
        { "name": "", "status": "open|closed|unknown", "id": "", "virtualrings": [], "vlans": x, "ringmembers": [], "errors": [] }
        """

        # if the result is known and refresh is not needed then just return the restul
        if self.logicalringinfo and not refresh:
            return self.logicalringinfo

        logicalrings = []
        # lr_rid = {}  # { 'rid': [], .. }  # keep track of unique LR names

        # weight: INFO, WARN, ERROR, CRITICAL
        #         0-4, 5-9, 10-14, 15-19
        def create_error_categories():
            return {
                "lldp_issues": {"count": 0, "weight": 5},
                "port_issues": {"count": 0, "weight": 5},
                "logical_ring_missing": {"count": 0, "weight": 5},
                "ring_naming_issues": {"count": 0, "weight": 10},
                "ring_open_issues": {"count": 0, "weight": 10},
            }

        for p in self.parserlist:
            pname = p.model.host.hostname
            pchassisid = p.model.host.chassisid
            # for lring in [ x for x in p.model.rings if x.type == 'logical-ring' ]:
            for lring in p.model.logical_rings():
                ## check each east + west port status
                rname = lring.name or UNKNOWN
                rid = lring.id or UNKNOWN
                # lr_rid.setdefault(rid, [])
                # lr_rid[rid].append(rname)
                rkey = "{}-{}".format(rname, rid)
                vrings = [
                    x.name if self._is_class(x) else x
                    for x in lring.virtualrings
                ] or []
                ## check if the ring already exists, if it does then add the ringmember, otherwise add the ring
                n = next(
                    iter(
                        list(
                            filter(
                                lambda x: "{}-{}".format(x["name"], x["id"])
                                == rkey,
                                logicalrings,
                            )
                        )
                    ),
                    None,
                )
                if n:
                    n["ringmembers"].append(p)
                    n["virtualrings"] = n["virtualrings"] + vrings
                else:
                    newring = {
                        "name": rname,
                        "status": UNKNOWN,
                        "ringnamekey": [],
                        "id": rid,
                        "virtualrings": vrings,
                        "ringmembers": [p],
                        "errors": [],
                        "errors_cat": create_error_categories(),
                    }
                    logicalrings.append(newring)

                # TODO:
                # ## keep track of unique logical-ring names, key = ringid-easttermination-westtermination
                # ##   this is done in the virtual-ring because the termination is only known here
                # if lr:
                #     lrid = lr['id']
                #     lringkey = "{}-{}-{}".format(lrid, self.coldelim.join(et), self.coldelim.join(wt))
                #     lr['ringnamekey'].append(lringkey)
                #     self.lringnames.setdefault(lringkey, [])
                #     self.lringnames[lringkey].append(lr['name'])
                #     print("lringkey = {}".format(lringkey))
                #     print("lr ringnamekey = {}".format(lr['ringnamekey']))
                #     #print("lringnames = {}".format(self.lringnames))

        # make unique strings in each list + check the ring status
        for lring in logicalrings:
            self._logical_ring_status(lring)
            lring["severity"] = self.get_severity_from_errors(
                lring["errors_cat"]
            )
            lring["virtualrings"] = list(set(lring["virtualrings"]))
            lring["ringmembers"] = list(
                set(
                    [
                        x.model.host.hostname if self._is_class(x) else x
                        for x in lring["ringmembers"]
                    ]
                )
            )

        self.logicalringinfo = {"logicalrings": logicalrings}

        # flat json reporting for easy import in splunk
        json_output = []
        for lr in self.logicalringinfo["logicalrings"]:
            json_output.append(
                json.dumps(lr, indent=4, separators=(",", ": "))
            )
        return "\n".join(json_output)

        # return json.dumps(self.logicalringinfo['logicalrings'], indent=4, separators=(',', ': '))

    def _virtual_ring_status(self, virtualring):
        """
        Define that status of a virtual ring:
        - there should be exactly 1 westport and 1 eastport termination - EXCEPTION: CORE RINGS !
        - virtual ring has to be attached to a logical ring
        - virtual ring members should be the same as logical ring members
        - a vlan in a virtual ring should exist on all ports in the logical ring and on all nodes in the same virtual ring
        - there should be at least 2 ring members
        - there should be at least 1 vlan
        - each vlan should be configured on each port of the logical ring
        - each vring should have exactly 1 rplowner
        - the rplowner should not be the same as eastport or westport termination
        - if the ringmembers only contain the termination hosts then rplowner = no
        - check vlan name: either have the vlan ID or the service id
        - check unique ring naming, 1 name per combination: RAPSVID-EASTTERMINATION-WESTTERMINATION
        """
        for rmember in virtualring["ringmembers"]:
            if not self._is_class(rmember):
                virtualring["errors"].append(
                    "{} - ring member {} is not an object".format(
                        virtualring["name"], rmember
                    )
                )
                virtualring["errors_cat"]["lldp_issues"]["count"] += 1
                continue
            mhostname = rmember.model.host.hostname
            # find the virtual ring for this member
            vr = next(
                iter(
                    list(
                        filter(
                            lambda x: (x.name == virtualring["name"])
                            and (x.type == "virtual-ring"),
                            rmember.model.rings,
                        )
                    )
                ),
                None,
            )
            ### ## check port termination
            ### if vr.subring == "east-port-termination":
            ###     if virtualring['easttermination']:
            ###         virtualring['errors'].append("{} - east-port-termination is defined multiple times, check {}".format(virtualring['name'], mhostname))
            ###         virtualring['errors_cat']['port_termination']['count'] += 1
            ###     else:
            ###         virtualring['easttermination'] = mhostname
            ### elif vr.subring == "west-port-termination":
            ###     if virtualring['westtermination']:
            ###         virtualring['errors'].append("{} - west-port-termination is defined multiple times, check {}".format(virtualring['name'], mhostname))
            ###         virtualring['errors_cat']['port_termination']['count'] += 1
            ###     else:
            ###         virtualring['westtermination'] = mhostname
            ## check logical ring
            lr_ports = []
            if not vr.logicalring:
                virtualring["errors"].append(
                    "{} - missing a logical ring, check {}".format(
                        virtualring["name"], mhostname
                    )
                )
                virtualring["errors_cat"]["logical_ring_missing"]["count"] += 1
            else:
                lr_ports = [vr.logicalring.eastport, vr.logicalring.westport]
            if len(lr_ports) < 2:
                virtualring["errors"].append(
                    "{} - the logical ring is missing east or west port on {}".format(
                        virtualring["name"], mhostname
                    )
                )
                virtualring["errors_cat"]["logical_ring_missing"]["count"] += 1
            ## check vlans (match on all nodes + exist on the logical ring ports)
            vr_vlans = [x.vlan if self._is_class(x) else x for x in vr.vlans]
            virtualring_vlans = [
                x.vlan if self._is_class(x) else x
                for x in virtualring["vlans"]
            ]
            if set(vr_vlans) != set(virtualring_vlans):
                # print("{} (vr: {}) - vlan difference: {}".format(mhostname, virtualring['name'], set(virtualring_vlans).symmetric_difference(set(vr_vlans)));
                virtualring["errors"].append(
                    "{} - the vlans do not match, check {}. Vlan diff = {}".format(
                        virtualring["name"],
                        mhostname,
                        set(virtualring_vlans).symmetric_difference(
                            set(vr_vlans)
                        ),
                    )
                )
                virtualring["errors_cat"]["vlan_issues"]["count"] += 1
            for vlan in vr.vlans:
                vlan_ports = vlan.ports if self._is_class(vlan) else None
                if not vlan_ports:
                    virtualring["errors"].append(
                        "{} - vlan {} is not configured on any ports on {}".format(
                            virtualring["name"], str(vlan), mhostname
                        )
                    )
                    virtualring["errors_cat"]["vlan_issues"]["count"] += 1
                # the vlan should be configured on at least the eastport + westport of the logical ring
                else:
                    vlan_ports = [
                        x.name if self._is_class(x) else x for x in vlan_ports
                    ]
                    lr_ports = [
                        x.name if self._is_class(x) else x for x in lr_ports
                    ]
                    # print("{} - vlan_ports =>> {}, lr_ports =>> {}".format(mhostname, vlan_ports, lr_ports))
                    port_diff = set(lr_ports) - set(vlan_ports)
                    if len(port_diff) > 0:
                        # print("{} - vlan {} is not configured on all the logical ring ports on {}".format(virtualring['name'], str(vlan), mhostname))
                        # print("- set(lr_ports) => {}".format(set(lr_ports)))
                        # print("- set(vlan_ports) => {}".format(set(vlan_ports)))
                        # print("- set(lr_ports) - set(vlan_ports) => {}".format(mhostname, set(lr_ports) - set(vlan_ports)))
                        # print("{} [vlan: {}, vr: {}, lr: {}] : vlan_ports =>> {}, lr_ports =>> {}".format(mhostname, str(vlan), virtualring['name'], vr.logicalring.name, vlan_ports, lr_ports))
                        virtualring["errors"].append(
                            "{} - vlan {} is not configured on all the logical ring ports on {} (lr ports: {}, missing ports: {})".format(
                                virtualring["name"],
                                str(vlan),
                                mhostname,
                                lr_ports,
                                port_diff,
                            )
                        )
                        virtualring["errors_cat"]["vlan_issues"]["count"] += 1

        ## don't give an error if the termination ports are set tot -none-
        if not (
            virtualring["easttermination"]
            == virtualring["westtermination"]
            == NONE
        ):
            # exceptions: do not throw errors for core rings
            if re.match("^[LV]R\-CMR[\-_]", virtualring["name"]):
                # do not throw an error
                pass
            else:
                if (
                    len(virtualring["easttermination"]) == 0
                    or len(virtualring["westtermination"]) == 0
                ):
                    virtualring["errors"].append(
                        "{} - port termination is missing".format(
                            virtualring["name"]
                        )
                    )
                    virtualring["errors_cat"]["port_termination"]["count"] += 1
                if (
                    len(virtualring["easttermination"]) > 1
                    or len(virtualring["westtermination"]) > 1
                ):
                    virtualring["errors"].append(
                        "{} - port termination is defined multiple times, check east-port-termination or west-port-termination".format(
                            virtualring["name"]
                        )
                    )
                    virtualring["errors_cat"]["port_termination"]["count"] += 1
        if len(virtualring["ringmembers"]) < 2:
            virtualring["errors"].append(
                "{} - not enough nodes in the ring".format(virtualring["name"])
            )
            virtualring["errors_cat"]["ring_members_issue"]["count"] += 1
        if len(virtualring["vlans"]) == 0:
            virtualring["errors"].append(
                "{} - no vlans configured".format(virtualring["name"])
            )
            virtualring["errors_cat"]["no_vlans_configured"]["count"] += 1

        ## TODO: add vlan naming check here
        ## each vlan can have either the vlan id or the VT reference, nothing else
        unique_vlans = {}
        for v in virtualring["vlans"]:
            if type(v) is str:
                virtualring["errors"].append(
                    "{} - vlan {} is not an objct".format(
                        virtualring["name"], v
                    )
                )
                virtualring["errors_cat"]["vlan_issues"]["count"] += 1
                continue
            unique_vlans.setdefault(str(v), [])
            unique_vlans[str(v)].append(v)
        for v in unique_vlans:
            if len(unique_vlans[v]) > 0:
                descr = None
                for v1 in unique_vlans[v]:
                    name = v1.name or None
                    if (descr is None) and name:
                        descr = name
                    elif name and name != descr:
                        # print("{} - vlan {}: naming or description inconsistency ({} vs {})".format(virtualring['name'], v1.vlan, name, descr))
                        virtualring["errors"].append(
                            "{} - vlan {}: naming or description inconsistency".format(
                                virtualring["name"], v1.vlan
                            )
                        )
                        virtualring["errors_cat"]["vlan_naming_issues"][
                            "count"
                        ] += 1

        virtualring_members = [
            x.model.host.hostname if self._is_class(x) else x
            for x in virtualring["ringmembers"]
        ]
        if set(virtualring_members) != set(virtualring["logicalringmembers"]):
            virtualring["errors"].append(
                "{} - the ring members do not match the logical ring members".format(
                    virtualring["name"]
                )
            )
            virtualring["errors_cat"]["ring_members_issue"]["count"] += 1

        # check rplowner (exactly 1, not the same as east or west termination)
        # if the ringmembers only contain the termination hosts then rplowner = no
        if (
            len(virtualring["easttermination"]) > 0
            and len(virtualring["westtermination"]) > 0
        ) and (
            set(virtualring_members)
            == set(
                virtualring["easttermination"] + virtualring["westtermination"]
            )
        ):
            virtualring["rplowner"] = ["no"]
        else:
            if len(virtualring["rplowner"]) != 1:
                virtualring["errors"].append(
                    "{} - rpl owner count is not correct ({})".format(
                        virtualring["name"], len(virtualring["rplowner"])
                    )
                )
                virtualring["errors_cat"]["rplowner_issues"]["count"] += 1
            for rplowner in virtualring["rplowner"]:
                if (rplowner in virtualring["easttermination"]) or (
                    rplowner in virtualring["westtermination"]
                ):
                    virtualring["errors"].append(
                        "{} - rpl owner should not be the same as east or west termination".format(
                            virtualring["name"], rplowner
                        )
                    )
                    virtualring["errors_cat"]["rplowner_issues"]["count"] += 1

        ### check unique ring name, 1 VR name per RAPSVID-easttermination-westtermination
        vrkey = virtualring["ringnamekey"]
        if not vrkey:
            virtualring["errors"].append(
                "{} - unable to check if the ringnamekey is unique, vrapsid or port termination is missing".format(
                    virtualring["name"]
                )
            )
            virtualring["errors_cat"]["ring_naming_issues"]["count"] += 1
        else:
            if vrkey in self.vringnames:
                if not (len(set(self.vringnames[vrkey])) == 1):
                    virtualring["errors"].append(
                        "{} - there is a problem with the virtual ring name, multiple vrings have the same ringnamekey ({}): {}".format(
                            virtualring["name"],
                            vrkey,
                            set(self.vringnames[vrkey]),
                        )
                    )
                    virtualring["errors_cat"]["ring_naming_issues"][
                        "count"
                    ] += 1

        ## TODO:
        ##   vring name syntax check

        ### rapsvid = virtualring['rapsvid'] or UNKNOWN
        ### easttermination = virtualring['easttermination'] or UNKNOWN
        ### westtermination = virtualring['westtermination'] or UNKNOWN
        ### unique_vring_id = "{}-{}-{}".format(rapsvid, easttermination, westtermination)
        ### if unique_vring_id and len(set(vr_rapsid.get(unique_vring_id, []))) != 1:
        ###     virtualring['errors'].append("{} - multiple VR names with the same RAPSVID {}: [{}], unique ringid = {} (east/west termination = {}/{})".format(virtualring['name'], virtualring['rapsvid'], ",".join( set(vr_rapsid.get(unique_vring_id, [])) ), unique_vring_id, easttermination, westtermination ))
        ###     virtualring['errors_cat']['ring_naming_issues']['count'] += 1

        ## set the ring status
        virtualring["status"] = self.get_ring_status_code(virtualring)
        # if len(virtualring['errors']) > 0:
        #     virtualring['status'] = "NOT OK"
        # else:
        #     virtualring['status'] = "OK"

    def get_virtual_ring_info(self, refresh=False):
        """
        Returns information per unique virtual ring in JSON format
        Unique key = ringname-rapsvid
        Returns:
        { "name": "", "rapsvid": "", vlans": [], "logicalring": "", "logicalringstatus": "", "ringmembers": [], "easttermination": "", "westtermination": "", "errors": [], "error_cat": { } }
        """

        # if the result is known and refresh is not needed then just return the restul
        if self.virtualringinfo and not refresh:
            return self.virtualringinfo

        # we need the logical ring info
        if not self.logicalringinfo:
            self.get_logical_ring_info(refresh=True)

        virtualrings = []
        self.vringnames = {}  # 'key': [ vringname ]
        self.lringnames = {}  # 'key': [ lringname ]
        # vr_rapsid = {}  # { 'rapsid-easttermination-westtermination': [], .. }  # keep track of unique VR names
        # weight: INFO, WARN, ERROR, CRITICAL
        #         0-4, 5-9, 10-14, 15-19
        def create_error_categories():
            return {
                "ring_members_issue": {"count": 0, "weight": 10},
                "no_vlans_configured": {"count": 0, "weight": 0},
                "port_termination": {"count": 0, "weight": 10},
                "vlan_issues": {"count": 0, "weight": 10},
                "vlan_naming_issues": {"count": 0, "weight": 0},
                "logical_ring_missing": {"count": 0, "weight": 10},
                "lldp_issues": {"count": 0, "weight": 10},
                "rplowner_issues": {"count": 0, "weight": 10},
                "ring_naming_issues": {"count": 0, "weight": 10},
            }

        for p in self.parserlist:
            pname = p.model.host.hostname
            pchassisid = p.model.host.chassisid
            # for vring in [ x for x in p.model.rings if x.type == 'virtual-ring' ]:
            for vring in p.model.virtual_rings():
                name = vring.name or UNKNOWN
                rapsvid = vring.rapsvid or UNKNOWN
                rplowner = vring.rplowner
                # termination = vring.subring or UNKNOWN
                eastport_termination = vring._eastport_termination
                westport_termination = vring._westport_termination
                vlans = vring.vlans
                logicalring = (
                    vring.logicalring.name
                    if self._is_class(vring.logicalring)
                    else vring.logicalring or UNKNOWN
                )
                ## find the logical ring from the logicalringinfo collection
                lr = next(
                    iter(
                        list(
                            filter(
                                lambda x: x["name"] == logicalring,
                                self.logicalringinfo["logicalrings"],
                            )
                        )
                    ),
                    None,
                )
                logicalringstatus = lr["status"] if lr else UNKNOWN
                logicalringmembers = lr["ringmembers"] if lr else []

                ## check if the ring already exists, if it does then add the ringmember, otherwise add the ring
                n = next(
                    iter(
                        list(
                            filter(
                                lambda x: "{}-{}".format(
                                    x["name"], x["rapsvid"]
                                )
                                == "{}-{}".format(name, rapsvid),
                                virtualrings,
                            )
                        )
                    ),
                    None,
                )
                ## TODO: add extra things like termination, rapsvid, ... ?
                ##       right now only the first SDS may be updated correctly
                if n:
                    n["ringmembers"].append(p)
                    n["vlans"] = n["vlans"] + vlans
                    n["rplowner"] = n["rplowner"] + rplowner
                    n["easttermination"] = (
                        n["easttermination"] + eastport_termination
                    )
                    n["westtermination"] = (
                        n["westtermination"] + westport_termination
                    )

                    ## keep track of unique vring names, key = rapsvid-easttermination-westtermination
                    et = set(n["easttermination"])
                    wt = set(n["westtermination"])
                    if n["rapsvid"] and (len(et) > 0) and (len(wt) > 0):
                        vringkey = "{}-{}-{}".format(
                            n["rapsvid"],
                            self.coldelim.join(et),
                            self.coldelim.join(wt),
                        )
                        n["ringnamekey"] = vringkey
                        self.vringnames.setdefault(vringkey, [])
                        self.vringnames[vringkey].append(n["name"])
                else:
                    newring = {
                        "name": name,
                        "ringnamekey": "",
                        "status": UNKNOWN,
                        "severity": UNKNOWN,
                        "rapsvid": rapsvid,
                        "rplowner": rplowner,
                        "vlans": vlans,
                        "ringmembers": [p],
                        "easttermination": eastport_termination,
                        "westtermination": westport_termination,
                        "logicalring": logicalring,
                        "logicalringstatus": logicalringstatus,
                        "logicalringmembers": logicalringmembers,
                        "errors": [],
                        "errors_cat": create_error_categories(),
                    }
                    virtualrings.append(newring)

        # make unique strings in each list + check the ring status
        for vring in virtualrings:
            self._virtual_ring_status(vring)
            ## don't use vlan name here, add extra check to show vlan naming inconstencies
            vring["vlans"] = list(
                set(
                    [
                        "{}".format(x.vlan) if self._is_class(x) else x
                        for x in vring["vlans"]
                    ]
                )
            )
            # vring['vlans'] = list(set([ "{} ({})".format(x.vlan, x.name or UNKNOWN) if self._is_class(x) else x for x in vring['vlans'] ]))
            vring["ringmembers"] = list(
                set(
                    [
                        x.model.host.hostname if self._is_class(x) else x
                        for x in vring["ringmembers"]
                    ]
                )
            )
            vring["easttermination"] = self.coldelim.join(
                list(set(vring["easttermination"]))
            )
            vring["westtermination"] = self.coldelim.join(
                list(set(vring["westtermination"]))
            )
            vring["severity"] = self.get_severity_from_errors(
                vring["errors_cat"]
            )

        # TODO
        # ## we need to loop again over all vrings because only at this point easttermination and westtermination are known
        # ##  and this is required to find unique ring names
        # for vring in virtualrings:
        #     name = vring['name'] or UNKNOWN
        #     rapsvid = vring['rapsvid'] or UNKNOWN
        #     easttermination = vring['easttermination'] or UNKNOWN
        #     westtermination = vring['westtermination'] or UNKNOWN
        #     unique_vring_id = "{}-{}-{}".format(rapsvid, easttermination, westtermination)
        #     vr_rapsid.setdefault(unique_vring_id, [])
        #     vr_rapsid[unique_vring_id].append(unique_vring_id)
        # print(vr_rapsid)

        self.virtualringinfo = {"virtualrings": virtualrings}
        # print(self.virtualringinfo)

        # flat json reporting for easy import in splunk
        json_output = []
        for vr in self.virtualringinfo["virtualrings"]:
            json_output.append(
                json.dumps(vr, indent=4, separators=(",", ": "))
            )
        return "\n".join(json_output)
        # return json.dumps(self.virtualringinfo['virtualrings'], indent=4, separators=(',', ': '))

    def report_virtual_ring_inventory(self):
        """
        Makes a CSV report for inventory of virtual rings, one line per RINGNAME-HOSTNAME combination
        columns: RINGNAME, STATUS, TYPE, HOSTNAME, MGMTIP, RAPSVID, VLANCOUNT, VLANS, EASTTERMINATION, WESTTERMINATION, RINGMEMBERCOUNT, RINGMEMBERS, LOGICALRING, LRINGSTATUS, LRMEMBERCOUNT, LOGICALRINGMEMBERS,
        """
        yield [
            "RINGNAME",
            "STATUS",
            "SEVERITY",
            "TYPE",
            "HOSTNAME",
            "MGMTIP",
            "RAPSVID",
            "RPLOWNER",
            "VLANCOUNT",
            "EASTTERMINATION",
            "WESTTERMINATION",
            "RINGMEMBERCOUNT",
            "RINGMEMBERS",
            "LOGICALRING",
            "LRSTATUS",
            "LRMEMBERCOUNT",
            "LRMEMBERS",
            "VLANS",
            "ERRORS",
            "ERR_RING_NAMING",
            "ERR_RINGMEMBERS",
            "ERR_NO_VLANS",
            "ERR_PRT_TERM",
            "ERR_VLAN",
            "ERR_VLAN_NAMING",
            "ERR_LR",
            "ERR_LLDP",
            "ERR_RPLOWNER",
        ]

        for vr in self.virtualringinfo["virtualrings"]:
            for host in vr.get("ringmembers"):
                hostobj = self.object_by_hostname(host)
                _severity = str(vr.get("severity"))
                _ringname = str(vr.get("name"))
                _status = str(vr.get("status"))
                _type = str("virtual-ring")
                _hostname = host
                _mgmtip = (
                    "" if not hostobj else hostobj.model.get_management_ip()
                )
                _rapsvid = str(vr.get("rapsvid"))
                _rplowner = str(self.coldelim.join(set(vr.get("rplowner"))))
                _vlancount = str(len(set(vr.get("vlans"))))
                _vlans = str(self.coldelim.join(set(vr.get("vlans"))))
                _easttermination = str(vr.get("easttermination"))
                _westtermination = str(vr.get("westtermination"))
                _ringmembercount = str(len(vr.get("ringmembers")))
                _ringmembers = str(self.coldelim.join(vr.get("ringmembers")))
                _logicalring = str(vr.get("logicalring"))
                _lrstatus = str(vr.get("logicalringstatus"))
                _lrmembercount = str(len(vr.get("logicalringmembers")))
                _lrmembers = str(
                    self.coldelim.join(vr.get("logicalringmembers"))
                )
                _errors = str(len(vr.get("errors")))
                _errors_ring_members = str(
                    vr["errors_cat"]["ring_members_issue"]["count"]
                )
                _errors_no_vlans = str(
                    vr["errors_cat"]["no_vlans_configured"]["count"]
                )
                _errors_port_termination = str(
                    vr["errors_cat"]["port_termination"]["count"]
                )
                _errors_vlan_issues = str(
                    vr["errors_cat"]["vlan_issues"]["count"]
                )
                _errors_vlan_naming_issues = str(
                    vr["errors_cat"]["vlan_naming_issues"]["count"]
                )
                _errors_lr_missing = str(
                    vr["errors_cat"]["logical_ring_missing"]["count"]
                )
                _errors_lldp = str(vr["errors_cat"]["lldp_issues"]["count"])
                _errors_rplowner = str(
                    vr["errors_cat"]["rplowner_issues"]["count"]
                )
                _errors_vr_naming_issues = str(
                    vr["errors_cat"]["ring_naming_issues"]["count"]
                )

                yield [
                    _ringname,
                    _status,
                    _severity,
                    _type,
                    _hostname,
                    _mgmtip,
                    _rapsvid,
                    _rplowner,
                    _vlancount,
                    _easttermination,
                    _westtermination,
                    _ringmembercount,
                    _ringmembers,
                    _logicalring,
                    _lrstatus,
                    _lrmembercount,
                    _lrmembers,
                    _vlans,
                    _errors,
                    _errors_vr_naming_issues,
                    _errors_ring_members,
                    _errors_no_vlans,
                    _errors_port_termination,
                    _errors_vlan_issues,
                    _errors_vlan_naming_issues,
                    _errors_lr_missing,
                    _errors_lldp,
                    _errors_rplowner,
                ]

    def report_logical_ring_inventory(self):
        """
        Makes a CSV report for inventory of logical rings, one line per RINGNAME-HOSTNAME combination
        columns: RINGNAME, RINGID, SITEID, DSRID, ASRID, VALIDRINGNAME, STATUS, TYPE, HOSTNAME, MGMTIP, LOCATION, RINGMEMBERS, VIRTUALRINGS, ERRORS
        """
        yield [
            "HOSTNAME",
            "MGMTIP",
            "RINGNAME",
            "RINGID",
            "SITEID",
            "DSRID",
            "ASRID",
            "LOCATION",
            "STATUS",
            "SEVERITY",
            "TYPE",
            "RINGMEMBERCOUNT",
            "RINGMEMBERS",
            "VIRTUALRINGCOUNT",
            "VIRTUALRINGS",
            "ERRORS",
            "ERR_RING_NAMING",
            "ERR_LLDP",
            "ERR_PORTS",
            "ERR_LR",
        ]

        for lr in self.logicalringinfo["logicalrings"]:
            for host in lr.get("ringmembers"):
                hostobj = self.object_by_hostname(host)
                _severity = str(lr.get("severity"))
                _hostname = host
                _mgmtip = (
                    "" if not hostobj else hostobj.model.get_management_ip()
                )
                _ringname = str(lr.get("name"))
                _ringid = str(lr.get("id"))
                lr_name_info = self._validate_logical_ring_name(_ringname)
                _siteid = lr_name_info["siteid"]
                _dsrid = lr_name_info["dsrid"]
                _asrid = lr_name_info["asrid"]
                _location = ""
                _status = str(lr.get("status"))
                _type = "logical-ring"
                _ringmembercount = str(len(lr.get("ringmembers")))
                _ringmembers = str(self.coldelim.join(lr.get("ringmembers")))
                _virtualringcount = str(len(lr.get("virtualrings")))
                _virtualrings = str(self.coldelim.join(lr.get("virtualrings")))
                _errors = str(len(lr.get("errors")))
                _errors_lldp = str(lr["errors_cat"]["lldp_issues"]["count"])
                _errors_port_issues = str(
                    lr["errors_cat"]["port_issues"]["count"]
                )
                _errors_lr_issues = str(
                    lr["errors_cat"]["logical_ring_missing"]["count"]
                )
                _errors_lr_naming_issues = str(
                    lr["errors_cat"]["ring_naming_issues"]["count"]
                )

                yield [
                    _hostname,
                    _mgmtip,
                    _ringname,
                    _ringid,
                    _siteid,
                    _dsrid,
                    _asrid,
                    _location,
                    _status,
                    _severity,
                    _type,
                    _ringmembercount,
                    _ringmembers,
                    _virtualringcount,
                    _virtualrings,
                    _errors,
                    _errors_lr_naming_issues,
                    _errors_lldp,
                    _errors_port_issues,
                    _errors_lr_issues,
                ]

    def _validate_logical_ring_name(self, ringname):
        """
        validates the virtual ring name: ex LR-ASR-ANT_14_31
        and checks if the format of the name is correct
        returns: { "chassistype": "ASR", "siteid": "ANT", "dsrid": "14", "asrid": "31", "compliant": true}
        """
        rex = re.compile(
            "^LR-(?P<chassistype>[AD]SR)-(?P<siteid>ANT|BRU|DWDM)_(?P<dsrid>[0-9]+)_(?P<asrid>[0-9]+)"
        )
        r = {
            "chassistype": "",
            "siteid": "",
            "dsrid": "",
            "asrid": "",
            "compliant": False,
        }
        m = rex.match(ringname)
        if m:
            r["chassistype"] = str(m.groupdict().get("chassistype"))
            r["siteid"] = str(m.groupdict().get("siteid"))
            r["dsrid"] = str(m.groupdict().get("dsrid"))
            r["asrid"] = str(m.groupdict().get("asrid"))
            r["compliant"] = True
            # print("SITEID = {}".format(r["siteid"]))
        return r

    def get_service_info(self, refresh=False):
        """
        Returns all the unique services, for each service we keep track of:
          serviceid = unique serviceid
          devices = list of network devices where the service is configured
          descriptions = list of descriptions of each occurring serviceid
          cfsid = list of customer facing services (= VT or GSID found in the vswitch description)
        """

        # if the result is known and refresh is not needed then just return the restul
        if self.serviceinfo and not refresh:
            return self.serviceinfo

        services = []

        for p in self.parserlist:
            pname = p.model.host.hostname
            for svc in p.model.services:
                serviceid = svc.serviceid
                description = svc.description
                try:
                    cfsid = svc.vswitch.serviceid
                except AttributeError:
                    cfsid = None

                # see if the service already exists
                n = next(
                    iter(
                        list(
                            filter(
                                lambda x: x["serviceid"] == serviceid, services
                            )
                        )
                    ),
                    None,
                )
                if n:
                    n["devices"].append(pname)
                    if description:
                        n["descriptions"].append(description)
                    if cfsid:
                        n["cfsid"].append(cfsid)
                else:
                    new_service = {
                        "serviceid": serviceid,
                        "devices": [pname],
                        "descriptions": [],
                        "cfsid": [],
                    }
                    if description:
                        new_service["descriptions"].append(description)
                    if cfsid:
                        new_service["cfsid"].append(cfsid)

                    services.append(new_service)

        self.serviceinfo = {
            "services": sorted(
                services, key=lambda k: k["serviceid"], reverse=False
            )
        }

        # print(self.virtualringinfo)
        return json.dumps(self.serviceinfo, indent=4, separators=(",", ": "))

    def report_service_inventory(self):
        """
        Makes a CSV report for vlan inventory, one line per vlan
        columns: VLANID, TYPE, VLANNAME, LR_NAME, LR_STATUS, VR_NAME, VR_STATUS, VSWITCH, DEVICES
        """
        fields = ["SERVICE", "DEVICES", "DESCRIPTIONS", "CFSID"]
        yield fields

        for v in self.serviceinfo["services"]:
            r = {}
            r["SERVICE"] = v.get("serviceid")
            r["DEVICES"] = str(self.coldelim.join(set(v.get("devices"))))
            r["DESCRIPTIONS"] = str(
                self.coldelim.join(set(v.get("descriptions")))
            )
            r["CFSID"] = str(self.coldelim.join(set(v.get("cfsid"))))

            # yield [ _vlan, _type, _name, _lr_name, _lr_status, _vr_name, _vr_status, _vswitch, _terminating_host, _terminating_port, _devices ]
            yield [str(r[f]) for f in fields]

    def _vlan_status(self, vlan):
        """
        Define checks for vlans
        """
        return

    def get_vlan_info(self, refresh=False):
        """
        Returns information per unique vlan in JSON format
        Unique key = s-<vlan>-<rapsvid> for s-vlans OR c-<vlan>-<device> for terminating vlans
        Returns:
        {  }
        """

        # if the result is known and refresh is not needed then just return the restul
        if self.vlaninfo and not refresh:
            return self.vlaninfo

        # we need the logical ring info
        if not self.virtualringinfo:
            self.get_virtual_ring_info(refresh=True)

        vlans = []

        # weight: INFO, WARN, ERROR, CRITICAL
        #         0-4, 5-9, 10-14, 15-19
        def create_error_categories():
            return {}

        # create or update a new entry
        #
        def _create_update(v):
            # check if the vlan already exists, if not then create a new vlan
            new_vlan = {
                "_id": "",
                "vlan": "",
                "name": "",
                "type": "",
                "vr_name": "",
                "vr_status": "",
                "lr_name": "",
                "lr_status": "",
                "ports": "",
                "vswitch": "",
                "terminating_port": "",
                "terminating_host": "",
            }
            for k in v.keys():
                new_vlan[k] = v[k]
            vlans.append(new_vlan)

        for p in self.parserlist:
            pname = p.model.host.hostname
            for v in p.model.vlans:
                vlan_id = v.vlan
                vlan_type = v.type
                name = v.name or UNKNOWN
                if "SVLAN" in vlan_type:
                    if len(v._virtualrings) > 0:
                        for vr in v._virtualrings:
                            vr_name = vr.name or UNKNOWN
                            vr_status = vr.ringstatus or UNKNOWN
                            vr_rapsvid = vr.rapsvid
                            lr_name = vr.logicalring.name or UNKNOWN
                            lr_status = vr.logicalring.ringstatus or UNKNOWN
                            new_vlan_name = "S-{}-{}".format(
                                vlan_id, vr_rapsvid
                            )
                            ports = ""
                            _create_update(
                                {
                                    "_id": new_vlan_name,
                                    "vlan": vlan_id,
                                    "name": name,
                                    "type": "SVLAN",
                                    "vr_name": vr_name,
                                    "vr_status": vr_status,
                                    "lr_name": lr_name,
                                    "lr_status": lr_status,
                                    "ports": ports,
                                }
                            )
                    else:
                        new_vlan_name = "S-{}".format(vlan_id)
                        _create_update(
                            {
                                "_id": new_vlan_name,
                                "vlan": vlan_id,
                                "name": name,
                                "type": "SVLAN",
                            }
                        )
                if "CVLAN" in vlan_type:
                    if len(v._vswitches) > 0:
                        for vs in v._vswitches:
                            vs_name = vs.name or UNKNOWN
                            new_vlan_name = "C-{}-{}".format(vlan_id, vs_name)
                            # print("{} - {} - {}".format(pname, name, vs_name))
                            try:
                                # TODO:  THIS FAILS, WHY EVAL HERE ????
                                ports = eval(str(vs.port)) or UNKNOWN
                                _create_update(
                                    {
                                        "_id": new_vlan_name,
                                        "vlan": vlan_id,
                                        "name": name,
                                        "type": "CVLAN",
                                        "vswitch": vs_name,
                                        "terminating_port": ports,
                                        "terminating_host": pname,
                                    }
                                )
                            except:
                                (
                                    exc_type,
                                    exc_value,
                                    exc_traceback,
                                ) = sys.exc_info()
                                # print "*** print_tb:"
                                traceback.print_tb(
                                    exc_traceback, limit=1, file=sys.stdout
                                )

        # make unique strings in each list + check the ring status
        for vlan in vlans:
            self._vlan_status(vlan)

        self.vlaninfo = {
            "vlans": sorted(vlans, key=lambda k: int(k["vlan"]), reverse=False)
        }

        # print(self.virtualringinfo)
        return json.dumps(self.vlaninfo, indent=4, separators=(",", ": "))

    def report_vlan_inventory(self):
        """
        Makes a CSV report for vlan inventory, one line per vlan
        columns: VLANID, TYPE, VLANNAME, LR_NAME, LR_STATUS, VR_NAME, VR_STATUS, VSWITCH, DEVICES
        """
        fields = [
            "VLAN",
            "TYPE",
            "NAME",
            "LR_NAME",
            "LR_STATUS",
            "VR_NAME",
            "VR_STATUS",
            "VSWITCH",
            "TERM_HOST",
            "TERM_PORT",
            "DEVICES",
        ]
        yield fields

        for v in self.vlaninfo["vlans"]:
            # print(v)
            r = {}
            r["VLAN"] = v.get("vlan")
            r["TYPE"] = v.get("type")
            r["NAME"] = v.get("name")
            r["LR_NAME"] = v.get("lr_name", "")
            r["LR_STATUS"] = v.get("lr_status", "")
            r["VR_NAME"] = v.get("vr_name", "")
            r["VR_STATUS"] = v.get("vr_status", "")
            r["VSWITCH"] = v.get("vswitch", "")
            r["DEVICES"] = str(self.coldelim.join([]))
            r["TERM_HOST"] = v.get("terminating_host", "")
            r["TERM_PORT"] = v.get("terminating_port", "")

            # yield [ _vlan, _type, _name, _lr_name, _lr_status, _vr_name, _vr_status, _vswitch, _terminating_host, _terminating_port, _devices ]
            yield [str(r[f]) for f in fields]

    def report_switchport_status(self, refresh=False):
        """
        Makes a CSV report for switch port information, one line per HOST-PORT
        columns: HOSTNAME, MGMTIP,
        """

        fields = [
            "HOSTNAME",
            "MGMTIP",
            "PORT",
            "ADMINSTATE",
            "CAPABILITY",
            "ADMINSPEEDDUPLEX",
            "OPERSTATE",
            "OPERSPEEDDUPLEX",
            "AUTONEG",
            "LINKSTATEDURATION",
            "DESCRIPTION",
            "LLDP",
            "RSTP",
            "STORMCONTROL",
            "XVRSTATUS",
            "LLDPNBR",
            "MTU",
            "EGRESS_QUEUE",
            "EGRESS_SHAPER",
            "TYPE",
            "VPLSPORTTYPE",
            "LAG_PORTS",
            "VLANS",
            "ERRORS",
            "ERR_VLAN",
            "ERR_MTU",
            "ERR_SPEED",
            "ERR_DUPLEX",
        ]
        yield fields

        for host in self.switchportinfo["nodes"]:
            HOSTNAME = host.get("hostname")
            hostobj = self.object_by_hostname(HOSTNAME)
            MGMTIP = (
                UNKNOWN if not hostobj else hostobj.model.get_management_ip()
            )

            for port in host.get("ports"):
                r = {}
                r["HOSTNAME"] = HOSTNAME
                r["MGMTIP"] = MGMTIP
                r["PORT"] = port.get("name", UNKNOWN) or NONE
                r["CAPABILITY"] = port.get("speedcapability", UNKNOWN) or NONE
                r["ADMINSTATE"] = port.get("adminstate", UNKNOWN) or NONE
                r["ADMINSPEEDDUPLEX"] = (
                    port.get("adminspeedduplex", UNKNOWN) or NONE
                )
                r["OPERSTATE"] = port.get("operstate", UNKNOWN) or NONE
                r["OPERSPEEDDUPLEX"] = (
                    port.get("operspeedduplex", UNKNOWN) or NONE
                )
                r["AUTONEG"] = port.get("autoneg", UNKNOWN) or "off"
                r["LINKSTATEDURATION"] = (
                    port.get("linkstateduration", UNKNOWN) or NONE
                )
                r["DESCRIPTION"] = port.get("description", UNKNOWN) or NONE
                r["LLDP"] = port.get("lldp", UNKNOWN) or NONE
                r["RSTP"] = port.get("rstp", UNKNOWN) or NONE
                r["STORMCONTROL"] = port.get("stormcontrol", UNKNOWN) or NONE
                r["XVRSTATUS"] = port.get("xsvrstatus", UNKNOWN) or NONE
                r["LLDPNBR"] = port.get("lldpnbr", UNKNOWN) or NONE
                r["MTU"] = port.get("mtu", UNKNOWN) or NONE
                r["EGRESS_QUEUE"] = port.get("egressqueue", UNKNOWN) or NONE
                r["EGRESS_SHAPER"] = port.get("egressshaper", UNKNOWN) or NONE
                r["VLANS"] = str(
                    self.coldelim.join(port.get("_vlans", []) or [])
                )
                r["TYPE"] = port.get("type", UNKNOWN) or NONE
                r["LAG_PORTS"] = str(
                    self.coldelim.join(port.get("ports", []) or [])
                )
                r["VPLSPORTTYPE"] = port.get("vplsporttype", UNKNOWN) or NONE
                r["ERRORS"] = str(len(port.get("errors")))
                r["ERR_VLAN"] = str(port["errors_cat"]["vlan_issues"]["count"])
                r["ERR_MTU"] = str(port["errors_cat"]["mtu_issues"]["count"])
                r["ERR_SPEED"] = str(
                    port["errors_cat"]["speed_issues"]["count"]
                )
                r["ERR_DUPLEX"] = str(
                    port["errors_cat"]["duplex_issues"]["count"]
                )

                # print(r)

                yield [r[f] for f in fields]

    def get_general_inventory(self):
        """ """
        inventory = {}
        for p in self.parserlist:
            hostname = str(p.model.host.hostname)
            mgmtip = str(p.model.get_management_ip())
            chassisid = str(p.model.host.chassisid)
            vendor = str(p.model.system.vendor)
            hwtype = str(p.model.system.hwtype)
            software = str(p.model.system.software)
            os = str(p.model.system.os)

            inventory[hostname] = {
                "mgmtip": mgmtip,
                "chassisid": chassisid,
                "vendor": vendor,
                "hwtype": hwtype,
                "software": software,
                "os": os,
            }

        return json.dumps(inventory, indent=4, separators=(",", ": "))

    def report_general_inventory(self):
        """
        Makes a CSV report with general inventory information:
        columns: HOSTNAME, MGMTIP, SNMP_COMMUNITY
        """

        yield [
            "HOSTNAME",
            "MGMTIP",
            "CHASSISID",
            "VENDOR",
            "HWTYPE",
            "SOFTWARE",
            "OS",
        ]

        for p in self.parserlist:
            hostname = str(p.model.host.hostname)
            mgmtip = str(p.model.get_management_ip())
            chassisid = str(p.model.host.chassisid)
            vendor = str(p.model.system.vendor)
            hwtype = str(p.model.system.hwtype)
            software = str(p.model.system.software)
            os = str(p.model.system.os)

            yield [hostname, mgmtip, chassisid, vendor, hwtype, software, os]

    def report_config_check(self):
        """
        Makes a CSV report with general configuration checks per device:
        columns: HOSTNAME, MGMTIP, SNMP, TACACS
        """

        yield ["HOSTNAME", "MGMTIP", "TACACS", "NTP"]

        for p in self.parserlist:
            hostname = str(p.model.host.hostname)
            mgmtip = str(p.model.get_management_ip())

            ## VERIFY TACACS
            check_server = set(p.model.tacacs.servers or []) == set(
                ["10.0.32.14", "10.0.96.14"]
            )
            check_accounting = (
                p.model.tacacs.accounting == "enable"
                and p.model.tacacs.accounting_session == "on"
                and p.model.tacacs.accounting_command == "on"
            )
            check_authorization = p.model.tacacs.authorization == "enable"
            tacacs = str(
                check_server and check_accounting and check_authorization
            )

            ## verify NTP
            ntp_servers = [x.ip for x in p.model.ntpservers]
            check_ntp = set(ntp_servers) == set(["10.0.32.19", "10.0.96.19"])
            ntp = str(check_ntp)

            yield [hostname, mgmtip, tacacs, ntp]
