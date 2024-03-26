from typing import Optional
from . import Device

"""
Physical Network Link module, defines the physical link constraints and capabilities for inter-devices links

Usage:

"""

class PhysicalNetworkLink:
    """
    Represents a physical link between two network devices.
    A PhysicalNetworkLink is defined as a link between two physical devices
    A Physical Network Link is plugged on two network interfaces (Will need to modify device description)
    For now, the Physical Link is plugged between two devices in a directional way, device IDs are not swappable
    """

    next_id = 0
    DEFAULT_BANDWIDTH = 1000 * 1024  # in KB/s
    DEFAULT_DELAY = 10.0 # in ms


    @classmethod
    def _generate_id(cls) -> int:
        """
        Generates an ID for a new PhysicalNetworkLink instance.

        Returns:
            int: The PhysicalNetworkLink ID.
        """

        result = cls.next_id
        cls.next_id +=1
        return result


    def __init__(self, device_1: Optional[Device] = None, device_2: Optional[Device] = None, size: int = -1, delay: float = DEFAULT_DELAY) -> None:
        """
        Initializes the device with basic values
        Assigns ID, initial position, resource values, routing table and resource limits
        """
        # ID setting
        self.id = PhysicalNetworkLink._generate_id()

        self.device_1 = device_1
        self.device_2 = device_2

        if self.device_1:
            self.device_1_id: int = self.device_1.id
        else:
            self.device_1_id = -1

        if self.device_2:
            self.device_2_id: int = self.device_2.id
        else:
            self.device_2_id = -1


        self.bandwidth: float = PhysicalNetworkLink.DEFAULT_BANDWIDTH # Bandwidth in KB/s
        self.delay: float = delay # Additionnal Delay, defined when creating the link, needs to be defined as a distance function
        self.bandwidth_use: float = 0.0

        if size > 0:
            self.set_link_id(self.device_1_id*size + self.device_2_id)


    def set_link_id(self, id):
        """
        Sets a Physical Link's ID by hand if necessary.
        Args:
            id : int
                New device ID
        Returns:
            None
        """
        self.id = id


    def get_origin(self) -> int:
        return self.device_1_id

    def get_destination(self) -> int:
        return self.device_2_id


    def set_physical_network_link_bandwidth(self, bandwidth: float):
        """
        Sets a Physical Link's Bandwidth (in kBytes/s)

        Args:
            bandwidth : float
                Physical link's bandwidth (in kBytes/s)
        """
        self.bandwidth = bandwidth


    def set_physical_network_link_delay(self, delay: float):
        """
        Sets a Physical Link's associated delay

        Args:
            delay : float
                Physical link's delay
        """
        self.delay = delay


    def get_physical_network_link_delay(self) -> float:
        """
        Returns the Physical Link's associated delay

        Returns:
            delay : float
                Physical link's delay
        """
        return self.delay


    def available_bandwidth(self) -> float:
        """
        Returns the Physical Link's available (unused) bandwidth (in kBytes/s)

        Returns:
            available_bandwidth : float
                Physical link's available bandwidth
        """
        return self.bandwidth - self.bandwidth_use


    def use_bandwidth(self, bandwidth_request: float) -> bool:
        """
        Allocates Physical Link's bandwidth based on bandwidth request (in kBytes/s)

        Args:
            bandwidth_request : float
                Necessary bandwidth to allocate (in kBytes/s)

        Returns:
            bool
                True if allocation possible and successfull, else False
        """
        if bandwidth_request < self.available_bandwidth():
            self.bandwidth_use += bandwidth_request
            return True
        else:
            return False


    def free_bandwidth(self, free_bandwidth_request: float):
        """
        Free a part of the Physical Link's bandwidth based on free bandwidth request (in kBytes/s)
        If requested bandwidth is superior to allocated bandwidth, bandwidth use is set to 0 instead of negative value

        Args:
            free_bandwidth_request : float
                Necessary bandwidth to free (in kBytes/s)
        """
        self.bandwidth_use = max(self.bandwidth_use-free_bandwidth_request, 0)


    def check_physical_link(self, device_1_id: int, device_2_id: int) -> bool:
        """
        Check if the associated link actually links the two given devices

        Args:
            device_1_id : int
            device_2_id : int
        """
        if self.device_1_id == device_1_id and self.device_2_id == device_2_id:
            return True
        return False