import re
from nmsnetlib.parsers.definitions.CienaSAOS import definition as SAOSdefinition
from nmsnetlib.parsers.definitions.CienaERS import definition as ERSdefinition
from nmsnetlib.parsers.definitions.CiscoIOS import definition as CiscoIOSdefinition
from nmsnetlib.models.carrierethernet import SAOSModel, ERSModel
from nmsnetlib.models.cpe import CiscoIOSModel
from nmsnetlib.parsers.blockparser import BlockParser, LineParser

#### import logging


#### logger = logging.getLogger(__name__)
#### #logger.setLevel(logging.DEBUG)
#### logger.setLevel(logging.CRITICAL)
#### screenformatter = logging.Formatter('%(asctime)s - %(name)s [%(lineno)d] - %(levelname)s - %(message)s')
#### logprinter = logging.StreamHandler()
#### logprinter.setFormatter(screenformatter)
#### logger.addHandler(logprinter)

UNKNOWN = '-unknown-'
NONE = '-none-'

class SAOSParser(BlockParser):

    def __init__(self, hostname=None, configfile="", keepemptyblocks=False, debug=False):
        super(SAOSParser, self).__init__(hostname, configfile, keepemptyblocks, model=SAOSModel(), debug=debug)
        #self.parser = "SAOSParser"

        # configuration file details
        #self.reConfigStart = re.compile("^! (?P<HWTYPE>[0-9]+) Configuration File")  ## how to recognize the start of a config file
        self.reConfigStart = re.compile("^! ### START OF CONFIG ###")
        self.reBlockStart = re.compile("^!{10,}$")  ## how to recognize the start of a new block
        self.reBlockName = re.compile("^! (?P<BLOCKNAME>[A-Z].*)$")
        self.reBlockEnd = re.compile("^$") ## a new block will be created at each reBlockStart, for the last block in the file we will detect an empty line otherwise it will not be processed
        #self.reBlockEnd = re.compile("^!$") ## how to recognize the end of a new block
        #self.BlockEndRepeat = 2  ## a block starts and ends with a single line with "!"
        self.reIgnoreLine = re.compile("^(!+)$")
        self.parseSingleLine = True ## if enabled then also parse lines outside blocks

        self.pdef = SAOSdefinition


    def _is_class(self, o):
        """
        Checks if a variable is a Class object (Class)
        Returns True if it is
                False if it's not
        """
        return True if hasattr(o, '__dict__') else False


    def _link_references(self):
        """
            Link strings to objects if possible.
            This function is called as last while parsing the config.
        """

        super(SAOSParser, self)._link_references()

        ## links inside subports (for 87xx)
        ##  - add parentport to the vlan ports
        ##  - link to parentport
        for sp in self.model.subports:
            # add parentport to the vlan ports
            for v in sp.vtags:
                vlan = next(iter(list(filter(lambda x: str(v) == str(x.vlan), self.model.vlans))), None)
                if vlan is not None:
                    vlan.ports.append(sp.parentport)

            # link to parentport
            pp = next(iter(list(filter(lambda x: str(sp.parentport) == str(x.name), self.model.switchports))), None)
            if pp is not None:
                sp.parentport = pp


        ## links inside virtual-switches
        ##  - virtual-interfaces (mainly for 87xx)
        ##  - vlans inside a VS are C-VLANS
        ##  - link the port  (TODO: should this be a list ?)
        ##  - link the virtual-circuit
        for vswitch in self.model.vswitches:
            # virtual-interfaces
            new_vi = []
            for vint in vswitch.virtualinterfaces:
                vi = next(iter(list(filter(lambda x: str(x.name) == str(vint), self.model.virtual_interfaces() ))), None)
                if vi is not None:
                    new_vi.append(vi)
                else:
                    new_vi.append(vint)
            vswitch.virtualinterfaces = new_vi

            # set vlan type to CVLAN
            # 
            ## TODO: CVLANS NORMALLY DON'T EXIST, ADD THEM HERE AS A CVLAN
            vlan = next(iter(list(filter(lambda x: str(x.vlan) == str(vswitch.vlan), self.model.vlans))), None)
            if vlan is not None:
                #print("vlan found '{}', {}".format(vswitch.vlan, vlan))
                vlan.type.append("CVLAN")
                vlan.type = list(set(vlan.type))
                vswitch.vlan = vlan
                vlan._vswitches.append(vswitch)
            else:
                ## TODO, create the vlan
                pass

            # link the port
            port = next(iter(list(filter(lambda x: str(x.name) == str(vswitch.port), self.model.switchports))), None)
            if port is not None:
                #print("vlan found '{}', {}".format(vswitch.vlan, vlan))
                vswitch.port = port

            # link the virtual-cicruit
            vcircuit = next(iter(list(filter(lambda x: str(x.name) == str(vswitch.vcircuit), self.model.vcircuits))), None)
            if vcircuit is not None:
                #print("vlan found '{}', {}".format(vswitch.vlan, vlan))
                vswitch.vcircuit = vcircuit



        ## links inside virtual-circuits
        ##   - vlans type = s-vlan
        for vcircuit in self.model.vcircuits:
            # set vlan type to SVLAN
            vlan = next(iter(list(filter(lambda x: str(x.vlan) == str(vcircuit.vlan), self.model.vlans))), None)
            if vlan is not None:
                #print("vlan found '{}', {}".format(vswitch.vlan, vlan))
                vlan.type.append("SVLAN")
                vlan.type = list(set(vlan.type))
                vcircuit.vlan = vlan


        ## links inside vlans
        ##   - link ports
        ##   - _vlans inside ports
        for vlan in self.model.vlans:
            # link the port
            new_ports = []
            for port in vlan.ports:
                p = next(iter(list(filter(lambda x: str(x.name) == str(port), self.model.switchports))), None)
                if p is not None:
                    new_ports.append(p)
                    # link the vlan in a switchport
                    p._vlans.append(vlan)
                else:
                    new_ports.append(port)

            vlan.ports = new_ports


        ## link the services to the vswitch
        for svc in self.model.services:
            vswitch = next(iter(list(filter(lambda x: str(x.name) == str(svc), self.model.vswitches))), None)
            if vswitch is not None:
                svc.vswitch = vswitch





        # link virtualinterfaces inside vswitch
        # for vswitch in self.model.vswitches:
        #     new_vi = []
        #     for vint in vswitch.virtualinterfaces:
        #         vi = next(iter(list(filter(lambda x: str(x.name) == str(vint), self.model.virtual_interfaces() ))), None)
        #         if vi:
        #             new_vi.append(vi)
        #         else:
        #             new_vi.append(vint)
        #     vswitch.virtualinterfaces = new_vi


        ## links inside virtual-rings
        ##   - link vswitches
        ##   - add vlans based on subports (for 87xx)
        ##   - vlans are of type SVLAN
        ##   - link to logical-ring
        ##   - set rpl-owner
        for vring in self.model.virtual_rings():

            # link the vswitches (TODO: is this correct for 87xx ??)
            new_vswitches = []
            for vswitch in vring.vswitches:
                vs = next(iter(list(filter(lambda x: str(x.name) == str(vswitch), self.model.vswitches))), None)
                if vs is not None:
                    #print("VIRTUAL SWITCH FOUND: {}".format(vs))
                    new_vswitches.append(vs)
                else:
                    new_vswitches.append(vswitch)
            vring.vswitches = new_vswitches

            # add S-vlans based on subports (for 87xx)
            # vswitch > virtualinterfaces > subports > vtag
            for vswitch in (vring.vswitches) :
                #vswitchobj = next(iter(list(filter(lambda x: str(x.name) == vswitch, self.model.vswitches))), None)
                if self._is_class(vswitch):
                    for vint in (vswitch.virtualinterfaces or []):
                        #print("subports: {}".format(self.model.subports))
                        subportobj = next(iter(list(filter(lambda x: str(x.name) == str(vint), self.model.subports))), None)
                        if not subportobj:
                            print("{} - {} - subport {} is not found".format(self.model.host.hostname, vring, vint))
                        else:
                            for vtag in (subportobj.vtags or []):
                                #print("{} - {} - {} - {} s-vlan found".format(self.model.host.hostname, vring, vint, vtag))
                                vring.vlans.append(vtag)

            # set vlan type to SVLAN
            new_vlans = []
            for vlan in vring.vlans:
                v = next(iter(list(filter(lambda x: str(x.vlan) == str(vlan), self.model.vlans))), None)
                if v is not None:
                    #print("VIRTUAL SWITCH FOUND: {}".format(vs))
                    v.type.append("SVLAN")
                    v.type = list(set(v.type))
                    v._virtualrings.append(vring)
                    new_vlans.append(v)
                else:
                    #vlan._virtualrings.append(vring)
                    new_vlans.append(vlan)
            vring.vlans = new_vlans

            # link to the logical ring
            lr = next(iter(list(filter(lambda x: x.type == 'logical-ring' and str(x.name) == str(vring.logicalring), self.model.rings))), None)
            if lr is not None:
                vring.logicalring = lr

            # set rplowner
            if len(vring.rplownerport) > 0:
                vring.rplowner.append(self.model.host.hostname)

            # set east-port-termination + west-port-termination
            if vring.subring == "east-port-termination":
                vring._eastport_termination.append(self.model.host.hostname)
            elif vring.subring == "west-port-termination":
                vring._westport_termination.append(self.model.host.hostname)
            ## the only exception is the VR-CMR_xxxx or VR-CMR-BRU-LAB_xxxx rings, this one does not have any termination port
            #if vring.name == 'VR-CMR_3801':
            if re.match("^VR-CMR(?:\-...\-LAB|\-LAB)?_", vring.name):
                vring._eastport_termination.append(NONE)
                vring._westport_termination.append(NONE)

            # make unique lists
            vring.vlans = list(set(vring.vlans))


        # ADD vlans to virtual-rings based on vtags in subports for SAOS87
        # vswitch > virtualinterfaces > subports > vtag
        # for vring in self.model.virtual_rings():
        #     #print("vring -> {}".format(vring))
        #     for vswitch in (vring.vswitches) :
        #         vswitchobj = next(iter(list(filter(lambda x: str(x.name) == vswitch, self.model.vswitches))), None)
        #         for vint in (vswitchobj.virtualinterfaces or []):
        #             #print("subports: {}".format(self.model.subports))
        #             subportobj = next(iter(list(filter(lambda x: str(x.name) == str(vint), self.model.subports))), None)
        #             if not subportobj:
        #                 print("{} - {} - subport {} is not found".format(self.model.host.hostname, vring, vint))
        #             else:
        #                 for vtag in (subportobj.vtags or []):
        #                     #print("{} - {} - {} - {} s-vlan found".format(self.model.host.hostname, vring, vint, vtag))
        #                     vring.vlans.append(vtag)
        #     vring.vlans = list(set(vring.vlans))


        # vlan in vswitches, type = c-vlan
        # for vswitch in self.model.vswitches:
        #     vlan = next(iter(list(filter(lambda x: str(x.vlan) == str(vswitch.vlan), self.model.vlans))), None)
        #     if vlan:
        #         #print("vlan found '{}', {}".format(vswitch.vlan, vlan))
        #         vswitch.vlan = vlan
        #         vlan.type.append("CVLAN")
        #         vlan.type = list(set(vlan.type))

        # ports in vswitches
        # for vswitch in self.model.vswitches:
        #     port = next(iter(list(filter(lambda x: str(x.name) == str(vswitch.port), self.model.switchports))), None)
        #     if port:
        #         #print("vlan found '{}', {}".format(vswitch.vlan, vlan))
        #         vswitch.port = port

        # ports in vlans
        # for vlan in self.model.vlans:
        #     new_ports = []
        #     for port in vlan.ports:
        #         p = next(iter(list(filter(lambda x: str(x.name) == str(port), self.model.switchports))), None)
        #         if p:
        #             new_ports.append(p)
        #         else:
        #             new_ports.append(port)
        #     vlan.ports = new_ports

        # vcircuits in vswitches
        # for vswitch in self.model.vswitches:
        #     vcircuit = next(iter(list(filter(lambda x: str(x.name) == str(vswitch.vcircuit), self.model.vcircuits))), None)
        #     if vcircuit:
        #         #print("vlan found '{}', {}".format(vswitch.vlan, vlan))
        #         vswitch.vcircuit = vcircuit


        ## links inside logical-rings
        ##   - link east-port and west-port
        ##   - link the virtual-ring

        for lring in self.model.logical_rings():

            # link east-port and west-port
            eastport = next(iter(list(filter(lambda x: str(x.name) == str(lring.eastport), self.model.switchports))), None)
            westport = next(iter(list(filter(lambda x: str(x.name) == str(lring.westport), self.model.switchports))), None)
            if eastport is not None:
                lring.eastport = eastport
            if westport is not None:
                lring.westport = westport


            # link the virtual-ring
            vr = next(iter(list(filter(lambda x: x.type == 'virtual-ring' and str(x.logicalring) == str(lring.name), self.model.rings))), None)
            if vr is not None:
                lring.virtualrings.append(vr)



        # eastport + westport in rings
        # for ring in [ x for x in self.model.rings if x.type == 'logical-ring' ]:
        #     eastport = next(iter(list(filter(lambda x: str(x.name) == str(ring.eastport), self.model.switchports))), None)
        #     westport = next(iter(list(filter(lambda x: str(x.name) == str(ring.westport), self.model.switchports))), None)
        #     if eastport:
        #         ring.eastport = eastport
        #     if westport:
        #         ring.westport = westport

        # vswitches in virtual-ring
        # for ring in [ x for x in self.model.rings if x.type == 'virtual-ring' ]:
        #     new_vswitches = []
        #     for vswitch in ring.vswitches:
        #         vs = next(iter(list(filter(lambda x: str(x.name) == str(vswitch), self.model.vswitches))), None)
        #         if vs:
        #             #print("VIRTUAL SWITCH FOUND: {}".format(vs))
        #             new_vswitches.append(vs)
        #         else:
        #             new_vswitches.append(vswitch)
        #     ring.vswitches = new_vswitches

        # vlans in virtual-ring, vlan type = s-vlan
        #for ring in [ x for x in self.model.rings if x.type == 'virtual-ring' ]:
        #    new_vlans = []
        #    for vlan in ring.vlans:
        #        v = next(iter(list(filter(lambda x: str(x.vlan) == str(vlan), self.model.vlans))), None)
        #        if v:
        #            #print("VIRTUAL SWITCH FOUND: {}".format(vs))
        #            new_vlans.append(v)
        #            v.type.append("SVLAN")
        #            v.type = list(set(v.type))
        #        else:
        #            new_vlans.append(vlan)
        #    ring.vlans = new_vlans

        # virtual-ring in logicalring
        # for ring in [ x for x in self.model.rings if x.type == 'logical-ring' ]:
        #     vr = next(iter(list(filter(lambda x: x.type == 'virtual-ring' and str(x.logicalring) == str(ring.name), self.model.rings))), None)
        #     if vr:
        #         ring.virtualrings.append(vr)

        # logicalring in virtual-ring
        # for ring in [ x for x in self.model.rings if x.type == 'virtual-ring' ]:
        #     lr = next(iter(list(filter(lambda x: x.type == 'logical-ring' and str(x.name) == str(ring.logicalring), self.model.rings))), None)
        #     if lr:
        #         ring.logicalring = lr

        # add hostname to rpl-owner if the virtual ring has an rplownerport set
        # for ring in [ x for x in self.model.rings if x.type == 'virtual-ring' ]:
        #     if len(ring.rplownerport) > 0:
        #         ring.rplowner.append(self.model.host.hostname)

        # LLDP
        ## TODO: can 1 port have multiple neighbors??
        ## TODO: all ports in a LAG port should have the same LLDP neighbor
        for lldp in self.model.lldpneighbors:
            #nbrport = next(iter(list(filter(lambda x: str(x.name) == str(lldp.nbrPort), self.model.switchports))), None)
            #print("localport before: {}".format(str(lldp.localPort)))
            l = list(set(filter(lambda x: str(x.name) == str(lldp.localPort), self.model.switchports)))
            #for i in self.model.switchports:
            #    print i.name
            localport = next(iter(list(filter(lambda x: str(x.name) == str(lldp.localPort), self.model.switchports))), None)
            #print("localport after: {}".format(localport))
            #if nbrport:
            #    lldp.nbrPort = nbrport
            #    nbrport.lldpnbr = lldp
            if localport is not None:
                lldp.localPort = localport
                # attach the lldp neighbor to the local port
                localport.lldpnbr = lldp
                # if the local port is member of a lag then also attach it to the lag
                lagports = list(filter(lambda x: (x.type == "L2 lag port") and (str(localport) in x.ports), self.model.switchports))
                for lp in lagports:
                    lp.lldpnbr = lldp


    #def _parse_config_start(self, line):
    #    """
    #    Check if a line matches the start of a configuration file
    #    Return values
    #        True: a start of the config was found
    #        False: a start of the config was not found
    #
    #    OVERRIDE THE MAIN BASE CLASS BECAUSE WE WANT TO FIND THE HWTYPE FROM THE SAME LINE
    #    """
    #    m = self.reConfigStart.match(line)
    #    if m:
    #        if 'HWTYPE' in m.groupdict():
    #            self.model.system.hwtype = m.group('HWTYPE')
    #            logger.debug("HWTYPE found: {}".format(self.model.system.hwtype))
    #    return super(SAOSParser, self)._parse_config_start(line)



class ERSParser(BlockParser):

    def __init__(self, hostname=None, configfile="", keepemptyblocks=False, debug=False):
        super(ERSParser, self).__init__(hostname, configfile, keepemptyblocks, model=ERSModel(), debug=debug)
        #self.parser = self.__class__.__name__

        # configuration file details
        self.reConfigStart = re.compile("config$")  ## how to recognize the start of a config file
        self.reConfigEnd = re.compile("back$")  ## how to recognize the start of a config file
        self.reBlockStart = re.compile("# +(?P<BLOCKNAME>[A-Z].+)$")  ## how to recognize the start of a new block
        self.reBlockName = re.compile("# +(?P<BLOCKNAME>[A-Z].+)$")
        #self.reBlockEnd = re.compile("#$") ## how to recognize the end of a new block
        #self.BlockEndRepeat = 2  ## a block starts and ends with a single line with "#"
        self.reIgnoreLine = re.compile("^(#+)$")
        self.parseSingleLine = False ## if enabled then also parse lines outside blocks

        self.pdef = ERSdefinition



class CiscoIOSParser(LineParser):

    def __init__(self, hostname=None, configfile="", debug=False):
        super(CiscoIOSParser, self).__init__(hostname, configfile, model=CiscoIOSModel(), debug=debug)
        #self.parser = self.__class__.__name__

        # configuration file details
        self.reConfigStart = re.compile("! ### START OF CONFIG ###$")  ## how to recognize the start of a config file
        self.reConfigEnd = re.compile("! ### END OF CONFIG ###")  ## how to recognize the start of a config file
        #self.reBlockStart = re.compile("# +(?P<BLOCKNAME>[A-Z].+)$")  ## how to recognize the start of a new block
        #self.reBlockName = re.compile("# +(?P<BLOCKNAME>[A-Z].+)$")
        #self.reBlockEnd = re.compile("[^ ]") ## how to recognize the end of a new block
        #self.BlockEndRepeat = 2  ## a block starts and ends with a single line with "#"
        #self.reIgnoreLine = re.compile("^(#+)$")
        #self.parseSingleLine = True ## if enabled then also parse lines outside blocks
        #self.stickyDynamicBlocks = True

        self.pdef = CiscoIOSdefinition






