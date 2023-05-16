class Environment(object):
    """The ``Environment`` class mostly serves as a structure for storing basic information about the environment
        Attributes:
        ----------
        current_time: int
            The date and time of the current event.
        devices: list of devices

        applications : list of Applications to deploy

        physical_network_links : list of physical network links
        """


    def __init__(self):
        self.current_time = 0
        self.applications = []
        self.devices = []
        self.physical_network_links = []


    def getApplicationByID(self, app_id):
        for application in self.applications:
            if application.id == app_id:
                return application


    def addApplication(self, application):
        """ Adds a new application to the applications list"""
        self.applications.append(application)


    def removeApplication(self, app_id):
        """ Removes an application based on its id"""
        self.applications = [application for application in self.applications if application.id != app_id]


    def getDevices(self):
        return self.devices


    def getDeviceByID(self, dev_id):
        for device in self.devices:
            if device.id == dev_id:
                return device


    def addDevice(self, device):
        """ Adds a new device to the devices list"""
        self.devices.append(device)
