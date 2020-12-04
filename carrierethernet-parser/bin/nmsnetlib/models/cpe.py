from nmsnetlib.models.models import BaseModel


class CiscoIOSModel(BaseModel):
    """
    Model class to store the objects of a Cisco IOS device
    """
    def __init__(self):
        super(CiscoIOSModel, self).__init__()
        self.system.vendor = "Cisco"
        self.system.os = "IOS"
