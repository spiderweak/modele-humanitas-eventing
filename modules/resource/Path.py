"""
Path module, defines the physical path between two devices
A path is necessary when allocating network resources between two physical devices hosting inter-connected application process

Usage:

"""

from modules.resource.Device import Device
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.Environment import Environment

from typing import List, Dict, Any, Union, Tuple

# Will need to refactor this to replace with number of devices
MAX_HOPS = 100

class Path:
    """
    Represents a virtual path between two devices in the network.

    Attributes:
        source_id (int): The ID of the source device.
        destination_id (int): The ID of the destination device.
        devices_path (List[int]): List of device IDs forming the path from source to destination.
        physical_links_path (List[int]): List of physical link IDs forming the path from source to destination.
    """

    def __init__(self) -> None:
        """
        Initializes the Path object with default attributes.
        """

        self.source_id: int = -1
        self.destination_id: int = -1

        # Devices path is a list of all the devices from source to destination, including source and destination
        self.devices_path: List[int] = []

        # Physical Links path is a list of all the physicalNetworkLink IDs corresponding to the path from source device to destination device
        self.physical_links_path: List[int] = []

    def setSourceID(self, device_source_id: int) -> None:
        """
        Set the source device ID for the path.

        Args:
            device_source_id (int): The ID of the source device.
        """
        self.source_id = device_source_id

    def setDestinationID(self, device_destination_id: int):
        """
        Set the destination device ID for the path.

        Args:
            device_destination_id (int): The ID of the destination device.

        """
        self.destination_id = device_destination_id

    def path_generation(self, env: Environment, device_source_id: int, device_destination_id: int):
        """
        Generates the list of devices and links on the path from source to destination.

        This method sets the source and destination IDs, and populates `devices_path`
        and `physical_links_path` based on the given Environment.

        Args:
            env (Environment): The simulation environment object.
            device_source_id (int): The ID of the source device.
            device_destination_id (int): The ID of the destination device.
        """
        # get Route from source to destination

        self.setSourceID(device_source_id)
        self.setDestinationID(device_destination_id)
        self.devices_path.append(device_source_id)

        device_source = env.getDeviceByID(device_source_id)
        next_hop_id = device_source.getRouteInfo(device_destination_id)[0]
        self.physical_links_path.append(device_source_id*len(env.devices)+next_hop_id)
        hops = 1

        while next_hop_id != device_destination_id and hops < MAX_HOPS:
            self.devices_path.append(next_hop_id)
            device_source = env.getDeviceByID(next_hop_id)
            next_hop_id = device_source.getRouteInfo(device_destination_id)[0]
            self.physical_links_path.append(device_source.getDeviceID()*len(env.devices)+next_hop_id)
            hops+=1

        if self.devices_path[-1] != device_destination_id:
            self.devices_path.append(device_destination_id)

    def minBandwidthAvailableonPath(self, env: Environment):
        """
        Calculates the minimum available bandwidth on the path.

        This method returns the minimum available bandwidth among all the physical
        links on the path, which can be used for maximal resource allocation.

        Args:
            env (Environment): The simulation environment object.

        Returns:
            float: The minimum available bandwidth on the path.
        """
        min_bandwidth_available = min(env.physical_network.links[path_id].availableBandwidth() for path_id in self.physical_links_path)
        return min_bandwidth_available
