import logging
import re


# TODO:  remove PE HW info from output


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


log = logging.getLogger("findhost.reporter")
h = NullHandler()
log.addHandler(h)


class Reporter(object):

    type = "csv"
    delim = "|"
    delim2 = ","
    report = []  # contains the generated report, each row = 1 interface object

    # TODO
    # 'CPE_MANAGED',

    header = {
        "hostname": "CE_HOSTNAME",
        "hostname_guess": "CE_HOSTNAME_GUESS",
        "pe_vrf": "VRF",
        "mgmt": "CPE_LOOPBACK",
        "allvt": "SERVICEID",
        "product": "PRODUCT",
        "cpe_wan_ip": "CPE_WAN_IP",
        "cpe_wan_subnet": "CPE_WAN_SUBNET",
        "cpe_wan_mask": "CPE_WAN_MASK",
        "cpe_multivrf": "CPE_MULTIVRF",
        "pe": "PE",
        "pe_intf": "PE_INT",
        "pe_qos_policy_in": "PE_QOS_POLICY_IN",
        "pe_qos_policy_out": "PE_QOS_POLICY_OUT",
        "cpe_backup": "CPE_BACKUP_CONFIG",
        "transmission": "CPE_TRANSMISSION",
        "info_from": "CPE_INFO_FROM",
        "hardware": "CPE_CHASSIS",
        "software": "CPE_SW_VERSION",
        "apn": "CPE_APN",
        "cellularimei": "CPE_CELLULAR_IMEI",
        "cellularimsi": "CPE_CELLULAR_IMSI",
        "cellularcellid": "CPE_CELLULAR_CELLID",
        "cellularoperator": "CPE_CELLULAR_OPERATOR",
        "ce_intf": "CPE_WAN_INT",
        "ce_vrf": "CPE_VRF",
        "cpe_qos_policy_in": "CPE_QOS_POLICY_IN",
        "cpe_qos_policy_out": "CPE_QOS_POLICY_OUT",
        "intf_function": "CPE_INTF_FUNCTION",
        "vendor": "CPE_VENDOR",
        "firstseen": "CPE_FIRSTSEEN",
        "lastseen": "CPE_LASTSEEN",
        "serial": "CPE_SERIAL",
        "vdsl_lp": "CPE_VDSL_LP",
        "vdsl_bw_down": "CPE_VDSL_BW_DOWNLOAD",
        "vdsl_bw_up": "CPE_VDSL_BW_UPLOAD",
        "vdsl_lp_updated": "CPE_VDSL_LP_UPDATED",  ## date when the LP was updated
    }
    # header_values = [ 'hostname', 'hostname_guess', 'product', 'intf_function', 'intf_type', 'transmission', 'mgmt', 'wan', 'pe', 'telnetok', 'allvt', 'pe_intf', 'pe_vrf', 'ce_intf', 'ce_vrf', 'test' ]
    # header_values = [ 'hostname', 'hostname_guess', 'mgmt', 'vt', 'product', 'pe', 'pe_intf', 'transmission', 'intf_function', 'intf_type', 'wan', 'telnetok', 'allvt', 'pe_intf', 'pe_vrf', 'ce_intf', 'ce_vrf', 'test' ]
    header_values = [
        "allvt",
        "hostname",
        "hostname_guess",
        "mgmt",
        "cpe_wan_ip",
        "cpe_wan_subnet",
        "cpe_wan_mask",
        "cpe_multivrf",
        "pe",
        "pe_intf",
        "pe_vrf",
        "pe_qos_policy_in",
        "pe_qos_policy_out",
        "transmission",
        "ce_intf",
        "ce_vrf",
        "intf_function",
        "vendor",
        "info_from",
        "hardware",
        "firstseen",
        "lastseen",
        "serial",
        "vdsl_lp",
        "vdsl_bw_down",
        "vdsl_bw_up",
        "vdsl_lp_updated",
        "software",
        "cpe_backup",
        "cpe_qos_policy_in",
        "cpe_qos_policy_out",
        "apn",
        "cellularimei",
        "cellularimsi",
        "cellularcellid",
        "cellularoperator",
    ]

    def __init__(self, obj):
        log.debug("New reporter object created")
        self.report.append(
            self.delim.join([self.header.get(i, i) for i in self.header_values])
        )
        for o in obj:
            for i in obj[o]:
                log.debug("Add interface to report on: %s" % o)
                all_values = self.find_variables(i)
                self.report.append(
                    self.delim.join([all_values.get(i, "") for i in self.header_values])
                )

    ## add
    def find_variables(self, obj):
        v = {}
        rtr = obj.rtr

        ## get hostname value
        if rtr.isCPE():
            v["hostname"] = str(rtr.GetProp("hostname"))

        ## get lastseen value
        if rtr.isCPE():
            v["lastseen"] = str(rtr.GetProp("lastseen"))

        ## get firstseen value
        if rtr.isCPE():
            v["firstseen"] = str(rtr.GetProp("firstseen"))

        ## get serialnumber value
        # if rtr.isCPE():
        #   v['serial'] = str(rtr.GetProp('serialnumber'))
        v["serial"] = str(rtr.GetProp("serialnumber"))

        ## get VDSL line profile value
        if rtr.isCPE():
            vdsl = rtr.getVdslLineProfile()
            # v['vdsl_lp'] = vdsl['LP']
            # v['vdsl_bw_down'] = vdsl['BW_DOWN']
            # v['vdsl_bw_up'] = vdsl['BW_UP']
            v["vdsl_lp_updated"] = rtr.GetProp("vdsllineprofileupdated")
            v["vdsl_lp"] = str(rtr.GetProp("vdsllineprofile"))
            v["vdsl_bw_down"] = str(rtr.GetProp("vdslbwdownload"))
            v["vdsl_bw_up"] = str(rtr.GetProp("vdslbwupload"))

        ## get cpe hardware type
        ## get cpe hardware type
        ## get cpe hardware type
        # if rtr.isCPE():
        #    v['hardware'] = str(rtr.GetProp('hardware'))
        v["hardware"] = str(rtr.GetProp("hardware"))

        ## get cpe software
        v["software"] = str(rtr.GetProp("software"))

        ## get cpe apn
        v["apn"] = str(rtr.GetProp("apn"))

        ## get cpe cellularimei
        v["cellularimei"] = str(rtr.GetProp("cellularimei"))

        ## get cpe cellularimsi
        v["cellularimsi"] = str(rtr.GetProp("cellularimsi"))

        ## get cpe cellularcellid
        v["cellularcellid"] = str(rtr.GetProp("cellularcellid"))

        ## get cpe cellularoperator
        v["cellularoperator"] = str(rtr.GetProp("cellularoperator"))

        ## get hostname_guess value
        v["hostname_guess"] = str(obj.hostname_guess)

        ## get product name
        v["product"] = str(obj.product_obj.product)

        ## get interface transmsission
        v["transmission"] = str(obj.product_obj.transmission)

        ## get the router vendor
        # if rtr.isCPE():
        #    v['vendor'] = str(rtr.GetProp('vendor'))
        v["vendor"] = str(rtr.GetProp("vendor"))

        ## where did we get the info from: CE or CPE
        # if rtr.isCPE():
        #    v['info_from'] = str(rtr.GetProp('function'))
        v["info_from"] = str(rtr.GetProp("function"))

        ## get interface type
        v["intf_type"] = str(obj.product_obj.type)

        ## get interface function
        v["intf_function"] = str(obj.product_obj.function)

        ## get the management/loopback ip's
        v["mgmt"] = self.delim2.join(
            set([str(m.network) for m in rtr.getMgmtInterfaces()])
        )

        ## get the WAN network range
        v["cpe_wan_ip"] = str(obj.ip)
        v["cpe_wan_subnet"] = str(obj.network)
        v["cpe_wan_mask"] = str(obj.mask)

        ## find PE router where this interface is connected to
        if rtr.isPE():
            v["pe"] = str(rtr.GetProp("hostname")).lower()
        else:
            v["pe"] = self.delim2.join(
                set(
                    [
                        str(m.rtr.GetProp("hostname")).lower()
                        for m in obj.pe_intf_objects
                    ]
                )
            )

        ## if the interface is from a CPE then it means that telnet succeeded, otherwise it's based on PE info without telnet
        # if rtr.GetProp("telnetok"):
        if rtr.isCPE():
            v["telnetok"] = "connected"
            v["cpe_backup"] = "YES"
        else:
            v["telnetok"] = "notconnected"
            v["cpe_backup"] = "NO"
        # if rtr.isCPE():
        #    v['telnetok'] = 'telnetok'
        # else:
        #    v['telnetok'] = 'telnetnotok'

        ## TODO: keep a parameter if VT is configured on interfaces?
        ## get a list of all VT's found in the interface descriptions
        # always use the VT on the interface itself
        v["allvt"] = obj.vt
        if rtr.isCPE():
            ## + try to find all VT's based on the PE interface descriptions
            v["allvt"] = v["allvt"] + obj.GetVTFromPEInterfaces()
            ## if no VT's found are found at all, then get all VT's based on other interfaces of the CPE
            if len(v["allvt"]) <= 0:
                v["allvt"] = v["allvt"] + rtr.GetAllVTFromRouter()
        v["allvt"] = self.delim2.join(sorted(set(v["allvt"])))

        ## find the PE interfaces for this interface
        if rtr.isPE():
            v["pe_intf"] = str(obj.intf)
        else:
            v["pe_intf"] = self.delim2.join(
                set([str(m.intf) for m in obj.pe_intf_objects])
            )

        ## get the CPE interface name
        if rtr.isCPE():
            v["ce_intf"] = str(obj.intf)

        if rtr.isCPE():
            v["cpe_multivrf"] = "YES" if rtr.is_multivrf else "NO"

        ## get the interface VRF
        if rtr.isPE():
            v["pe_vrf"] = str(obj.vrf)
        else:
            v["ce_vrf"] = str(obj.vrf)
            v["pe_vrf"] = self.delim2.join(
                set([str(m.vrf) for m in obj.pe_intf_objects])
            )

        ## check QOS policies
        if rtr.isCPE():
            v["cpe_qos_policy_in"] = str(obj.policy_in)
            v["cpe_qos_policy_out"] = str(obj.policy_out)
            v["pe_qos_policy_in"] = self.delim2.join(
                set([str(m.policy_in) for m in obj.pe_intf_objects])
            )
            v["pe_qos_policy_out"] = self.delim2.join(
                set([str(m.policy_out) for m in obj.pe_intf_objects])
            )
        else:
            v["pe_qos_policy_in"] = str(obj.policy_in)
            v["pe_qos_policy_out"] = str(obj.policy_out)
            v["cpe_qos_policy_in"] = ""
            v["cpe_qos_policy_out"] = ""

        ### make sure the column values don't contain the delimiter values, replace them by _
        for k in v:
            v[k] = v[k].replace(self.delim, "_")
            # v[k] = v[k].replace(self.delim2, "_")

        return v

        self.report.append(self.delim.join(cols))
