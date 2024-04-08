"""
Path module, defines the physical path between two devices
A path is necessary when allocating network resources between two physical devices hosting inter-connected application process

Usage:

"""
from collections import deque

from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink

from typing import List, Dict, Any, Union, Tuple, Optional

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

    def __init__(self, device_source_id: int = -1, device_destination_id: int = -1) -> None:
        """
        Initializes the Path object with default attributes.
        """

        self.source_id = device_source_id
        self.destination_id = device_destination_id

        # Devices path is a list of all the devices from source to destination, including source and destination
        self.devices_path: deque[int] = deque()

        # Physical Links path is a list of all the physicalNetworkLink IDs corresponding to the path from source device to destination device
        self.physical_links_path: deque[int] = deque()

    def __eq__(self, other) -> bool:
        if self.source_id == -1 or self.destination_id == -1:
            return False

        return ((
                (self.source_id == other.source_id and
                self.destination_id == other.destination_id)
                )
                and
                set(self.devices_path) == set(other.devices_path)
                and
                set(self.physical_links_path) == set(other.physical_links_path)
                )

    @property
    def source_id(self):
        return self._source_id

    @source_id.setter
    def source_id(self, device_source_id: int):
        """
        Set the source device ID for the path.

        Args:
            device_source_id (int): The ID of the source device.
        """
        self._source_id = device_source_id

    @property
    def destination_id(self):
        return self._destination_id

    @destination_id.setter
    def destination_id(self, device_destination_id: int):
        """
        Set the destination device ID for the path.

        Args:
            device_destination_id (int): The ID of the destination device.

        """
        self._destination_id = device_destination_id

    def path_generation(self, env, device_source_id: int, device_destination_id: int):
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

        self.source_id = device_source_id
        self.destination_id = device_destination_id
        self.devices_path.append(device_source_id)

        device_source = env.get_device_by_id(device_source_id)
        next_hop_id = device_source.get_route_info(device_destination_id)[0]
        self.physical_links_path.append(device_source_id*len(env.devices)+next_hop_id)
        hops = 1

        while next_hop_id != device_destination_id and hops < MAX_HOPS:
            self.devices_path.append(next_hop_id)
            device_source = env.get_device_by_id(next_hop_id)
            next_hop_id = device_source.get_route_info(device_destination_id)[0]
            self.physical_links_path.append(device_source.id*len(env.devices)+next_hop_id)
            hops+=1

        if self.devices_path[-1] != device_destination_id:
            self.devices_path.append(device_destination_id)

    def min_bandwidth_available_on_path(self, env):
        """
        Calculates the minimum available bandwidth on the path.

        This method returns the minimum available bandwidth among all the physical
        links on the path, which can be used for maximal resource allocation.

        Args:
            env (Environment): The simulation environment object.

        Returns:
            float: The minimum available bandwidth on the path.
        """
        min_bandwidth_available = min(env.physical_network.links[path_id].available_bandwidth() for path_id in self.physical_links_path)
        return min_bandwidth_available

def path_append_left(physical_link: PhysicalNetworkLink, old_path: Optional[Path]):
    if physical_link.origin == physical_link.destination:
        return old_path

    if old_path is None:
        new_path = Path(physical_link.origin, physical_link.destination)
        new_path.devices_path.appendleft(new_path.destination_id)
        new_path.devices_path.appendleft(new_path.source_id)
        new_path.physical_links_path.appendleft(physical_link.id)
    else:
        new_path = Path(physical_link.origin, old_path.destination_id)
        new_path.devices_path = old_path.devices_path.copy()
        new_path.devices_path.appendleft(new_path.source_id)
        new_path.physical_links_path.appendleft(physical_link.id)

    if new_path.source_id == new_path.destination_id:
        new_path.devices_path = deque([new_path.source_id])
        new_path.physical_links_path = deque()
        print(f"Updated : {new_path.devices_path}")

    return new_path