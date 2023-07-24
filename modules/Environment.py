from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Application import Application
from modules.CustomExceptions import NoRouteToHost


from modules.ResourceManagement import custom_distance

import logging
import json
from tqdm import tqdm

class Environment(object):
    """
    The ``Environment`` class mostly serves as a structure for storing information about the environment (configuration, device info, application info, network link...)

    Attributes:
    -----------
    current_time: `int`
        The date and time of the current event.
    config: `Config`
        Environment configuration exported from the ``Config`` class
    devices : list of `Device`
        List of ``Device`` objects storing device information (position, resource availability, routing table...)
    applications: list of `Application` to deploy
        List of ``Application`` objects storing application information (processus, virtual links... )
    physical_network_links: list of physical network links
        List of Physical links between devices, connectivity matrix
    """


    def __init__(self):
        """
        The ``Environment`` class is initialized to empty lists, None or 0 values
        """

        self.current_time = 0

        self.config = None

        self.applications = []
        self.devices = []
        self.physical_network_links = [0]
        self.count_rejected_application=[[0,0]]

        self.TIME_PERIOD = 24 * 60 * 60 * 100



    def setConfig(self, config):
        """
        Sets the configuration based on a given instanciated `Config` class.

        Args:
        -----
        config: `Config`
            Environment configuration generated in the `Config` module
        """
        self.config = config


    def getDevices(self):
        return self.devices


    def getDeviceByID(self, dev_id):
        """
        Gets the first `Device` which ID matches `dev_id`.
        `Device` IDs are supposed to be unique by construction.

        Args:
        -----
        dev_id: `int`
            device identifier
        """
        for device in self.devices:
            if device.id == dev_id:
                return device


    def addDevice(self, device):
        """ Adds a new `Device` to the devices list"""
        self.devices.append(device)


    def getApplicationByID(self, app_id):
        """
        Gets the first `Application` which ID matches `app_id`.
        `Application` IDs are supposed to be unique by construction.
        """
        for application in self.applications:
            if application.id == app_id:
                return application


    def addApplication(self, application):
        """ Adds a new `Application` to the applications list"""
        self.applications.append(application)


    def removeApplication(self, app_id):
        """
        Removes all `Application` with given `app_id`
        `Application` IDs are supposed to be unique, so only one app should be removed
        """
        self.applications = [application for application in self.applications if application.id != app_id]

    def generateApplicationList(self):
        for i in tqdm(range(self.config.number_of_applications)):
            # Generating 1 random application
            application = Application()
            application.randomAppInit()
            application.setAppID(i)
            if self.config.app_duration != 0:
                application.setAppDuration(self.config.app_duration)

            self.applications.append(application)

    # Let's try to code a routing table
    def generate_routing_table(self):
        """
        Generates a routing table on each device in `self.devices`
        The function first lists the neighboring device, then iterate on the list to build a routing table based on shortest distance among links
        This is bruteforcing the shortest path betweend devices, we can probably create a better algorithm, but this is not the point for now.
        """

        number_of_devices = len(self.getDevices())

        self.physical_network_links = [0] * number_of_devices * number_of_devices

        for device_1 in self.getDevices():
            device_1_id = device_1.getDeviceID()
            for device_2 in self.getDevices():
                device_2_id = device_2.getDeviceID()
                distance = custom_distance(device_1.position.values(),device_2.position.values())
                new_physical_network_link_id = device_1_id*number_of_devices + device_2_id
                if distance < self.config.wifi_range:
                    device_1.addToRoutingTable(device_2_id, device_2_id, distance)
                    device_2.addToRoutingTable(device_1_id, device_1_id, distance)
                    new_physical_network_link = PhysicalNetworkLink(device_1_id, device_2_id)
                    new_physical_network_link.setLinkID(new_physical_network_link_id)
                    if device_1_id == device_2_id:
                        new_physical_network_link.setPhysicalNetworkLinkLatency(0)
                    self.physical_network_links[new_physical_network_link_id] = new_physical_network_link
                else:
                    new_physical_network_link = PhysicalNetworkLink()
                    self.physical_network_links[new_physical_network_link_id] = None

        ## We iterate on the matrix:

        changes = True

        # Approximative number of loops
        logging.info("Generating routing table")
        print("Generating Routing Table, (maximal value is arbitrary)")
        progress_bar = tqdm(total=int(number_of_devices*number_of_devices*1.5))

        while(changes):
            ## As long as the values change
            changes = False
            for i in range(number_of_devices):
                for j in range(number_of_devices):
                    device_i = self.getDeviceByID(i)
                    device_j = self.getDeviceByID(j)

                    try:
                        next_hop,distance = device_i.getRouteInfo(device_j.id)
                    except NoRouteToHost:
                        next_hop,distance = (-1,1000)

                    nh_array = [next_hop]
                    dist_array = [distance]
                    for k in range(number_of_devices):
                        device_k = self.getDeviceByID(k)
                        try:
                            next_hop_i_k,distance_i_k = device_i.getRouteInfo(device_k.id)
                        except NoRouteToHost:
                            next_hop_i_k,distance_i_k = (-1,1000)

                        try:
                            _,distance_k_j = device_k.getRouteInfo(device_j.id)
                        except NoRouteToHost:
                            distance_k_j = 1000

                        nh_array.append(next_hop_i_k)
                        dist_array.append(distance_i_k + distance_k_j)

                    min_index = dist_array.index(min(dist_array))
                    min_nh = nh_array[min_index]
                    min_array = dist_array[min_index]

                    if min_array < distance:
                    ## If we observe any change, update and break the loop, keep going
                        changes = True
                        progress_bar.update()
                        device_i.addToRoutingTable(device_j.id, min_nh, min_array)


    def export_devices(self, filename = "devices.json"):
        json_string = json.dumps(self.devices, default=lambda o: o.__json__(), indent=4)
        with open(filename, 'w') as file:
            file.write(json_string)

    def  export_applications(self, filename = "applications.json"):
        json_string = json.dumps(self.applications, default=lambda o: o.__json__(), indent=4)
        with open(filename, 'w') as file:
            file.write(json_string)