"""
Path module, defines the physical path between two devices
A path is necessary when allocating network resources between two physical devices hosting inter-connected application process

Usage:

"""

from modules.Device import Device
from modules.PhysicalNetworkLink import PhysicalNetworkLink

class Path:

    def __init__(self) -> None:
        """
        Initializes the Path with default values.
        Assigns Source and destination ID to placeholders.
        Initialises lists to empty values.

        Args:
            None

        Returns:
            None
        """
        self.source_id = -1
        self.destination_id = -1

        # Devices path is a list of all the devices from source to destination, including source and destination
        self.devices_path = list()

        # Physical Links path is a list of all the physicalNetworkLink IDs corresponding to the path from source device to destination device
        self.physical_links_path = list()

    def setSourceID(self, device_source_id):
        """
        Sets the ID associated with the source device

        Args:
            device_source_id : int, device source ID

        Returns:
            None
        """
        self.source_id = device_source_id

    def setDestinationID(self, device_destination_id):
        """
        Sets the ID associated with the destination device

        Args:
            device_destination_id : int, device destination ID

        Returns:
            None
        """
        self.destination_id = device_destination_id

    def path_generation(self, env, device_source_id, device_destination_id):
        """
        Generates both the list of devices on the path from source to destination and the list of links on this same path.

        Args:
            env : Environment
            device_source_id : int, device source ID
            device_destination_id : int, device destination ID

        Returns:
            None
        """
        # get Route from source to destination

        device_source = env.getDeviceByID(device_source_id)

        self.setSourceID(device_source_id)
        self.setDestinationID(device_destination_id)

        self.devices_path.append(device_source_id)
        next_hop_id = device_source.getRouteInfo(device_destination_id)[0]

        self.physical_links_path.append(device_source_id*len(env.devices)+next_hop_id)

        hops = 1

        while next_hop_id != device_destination_id and hops <100:
            self.devices_path.append(next_hop_id)
            device_source = env.getDeviceByID(next_hop_id)
            next_hop_id = device_source.getRouteInfo(device_destination_id)[0]
            self.physical_links_path.append(device_source.getDeviceID()*len(env.devices)+next_hop_id)
            hops+=1

        if self.devices_path[-1] != device_destination_id:
            self.devices_path.append(device_destination_id)

    def minBandwidthAvailableonPath(self, env):
        """
        Sets the ID associated with the destination device

        Args:
            env: Environment

        Returns:
            min_bandwidth_available : float, minimum value for all the available network resources (bandwidth) on the path. Used to determine maximal allocation value.
        """
        min_bandwidth_available = min(env.physical_network_links[path_id].availableBandwidth() for path_id in self.physical_links_path)
        return min_bandwidth_available
