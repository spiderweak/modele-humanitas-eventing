from modules.PhysicalNetworkLink import PhysicalNetworkLink
from modules.CustomExceptions import NoRouteToHost

# GLOBAL VARIABLES (bad practice)
wifi_range = 9


def custom_distance(x1, y1, z1, x2, y2, z2):
    """
    Defines a custom distance for device wireless coverage to account for less coverage due to floor interception.

    Args:
        x1 : x value, device 1
        z1 : z value, device 1
        y1 : y value, device 1
        x2 : x value, device 2
        y2 : y value, device 2
        z2 : z value, device 2

    Returns:
        distance : int, distance (as coverage) between device 1 and device 2.
    """
    distance = ((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)**0.5
    return distance


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

    # Let's try to code a routing table
    def generate_routing_table(env):
        """
        Generates a routing table on each device
        The function first lists the neighboring device, then iterate on the list to build a routing table based on shortest distance among links

        Args:
            env : Environment

        Returns:
            None
        """

        number_of_devices = len(env.devices)

        physical_network_link_list = [0]*number_of_devices*number_of_devices

        for device_1 in env.devices:
            device_1_id = device_1.getDeviceID()
            for device_2 in env.devices:
                device_2_id = device_2.getDeviceID()
                distance = custom_distance(device_1.x,device_1.y,device_1.z,device_2.x,device_2.y,device_2.z)
                new_physical_network_link_id = device_1_id*number_of_devices + device_2_id
                if distance < wifi_range:
                    device_1.addToRoutingTable(device_2_id, device_2_id, distance)
                    device_2.addToRoutingTable(device_1_id, device_1_id, distance)
                    new_physical_network_link = PhysicalNetworkLink(device_1_id, device_2_id)
                    new_physical_network_link.setLinkID(new_physical_network_link_id)
                    if device_1_id == device_2_id:
                        new_physical_network_link.setPhysicalNetworkLinkLatency(0)
                    physical_network_link_list[new_physical_network_link_id] = new_physical_network_link
                else:
                    new_physical_network_link = PhysicalNetworkLink()
                    physical_network_link_list[new_physical_network_link_id] = None

        ## We iterate on the matrix:

        changes = True

        while(changes):
            ## As long as the values change
            changes = False
            for i in range(number_of_devices):
                for j in range(number_of_devices):
                    device_i = env.getDeviceByID(i)
                    device_j = env.getDeviceByID(j)

                    try:
                        next_hop,distance = device_i.getRouteInfo(device_j.id)
                    except NoRouteToHost:
                        next_hop,distance = (-1,1000)

                    nh_array = [next_hop]
                    dist_array = [distance]
                    for k in range(number_of_devices):
                        device_k = env.getDeviceByID(k)
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
                    ## If we observe any change, update and break the loop
                        changes = True
                        device_i.addToRoutingTable(device_j.id, min_nh, min_array)

