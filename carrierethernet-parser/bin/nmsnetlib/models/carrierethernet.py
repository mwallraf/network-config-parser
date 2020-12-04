from nmsnetlib.models.models import BaseModel

class SAOSModel(BaseModel):
    """
    Model class to store the objects of a Ciena SAOS Carrier Ethernet Device
    """
    def __init__(self):
        super(SAOSModel, self).__init__()
        self.system.vendor = "Ciena"
        self.system.os = "SAOS"

    def get_management_ip(self):
        """
            Finds the local(outband) and remote(inband) ip addresses
            Returns { "inband": <ip>, "outband": <ip> }
        """
        super(SAOSModel, self).get_management_ip()
        mgmt = { "inband": "", "outband": "" }
        intlist = list(filter(lambda x: x.type == 'remote' or x.type == 'local', self.interfaces))
        for i in intlist:
            if i.ip and i.type == "remote":
                mgmt["inband"] = i.ip
            elif i.ip and i.type == "local":
                mgmt["outband"] = i.ip                
        return mgmt["inband"] or mgmt["outband"]


class ERSModel(BaseModel):
    """
    Model class to store the objects of a Ciena ERS Carrier Ethernet Device
    """
    def __init__(self):
        super(ERSModel, self).__init__()
        self.system.vendor = "Ciena"
        self.system.os = "ERS"
