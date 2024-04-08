"""
Physical Network Link module, defines the physical link constraints and capabilities for inter-devices links

Usage:

"""
from __future__ import annotations

from modules.resource.LinkMetric import LinkMetric, OSPFLinkMetric

class PhysicalNetworkLink:
    """
    Represents a physical link between two network devices.
    A PhysicalNetworkLink is defined as a link between two physical devices
    A Physical Network Link is plugged on two network interfaces (Will need to modify device description)
    For now, the Physical Link is plugged between two devices in a directional way, device IDs are not swappable
    """

    next_id = 0
    DEFAULT_BANDWIDTH = 100  # in MB/s
    DEFAULT_DELAY = 0.0 # in ms
    DEFAULT_DISTANCE = 0.0

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


    def __init__(self, metric_type = LinkMetric, device_1_id: int = -1, device_2_id: int = -1, size: int = -1, distance: float = DEFAULT_DISTANCE, delay: float = DEFAULT_DELAY) -> None:
        """
        Initializes the device with basic values
        Assigns ID, initial position, resource values, routing table and resource limits
        """
        self.metric_type = metric_type

        # ID setting
        self.id = PhysicalNetworkLink._generate_id()
        self.origin = device_1_id
        self.destination = device_2_id

        self.distance = distance
        self.bandwidth = PhysicalNetworkLink.DEFAULT_BANDWIDTH # Bandwidth in MB/s
        self.delay = delay # Additionnal Delay, defined when creating the link, needs to be defined as a distance function
        self.bandwidth_use: float = 0.0

        if size > 0:
            self.id = device_1_id*size + device_2_id

        try:
            self.metric = self.metric_type(self.bandwidth, self.distance, self.delay) # type:ignore
        except:
            raise


    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, id):
        """
        Sets a Physical Link's ID by hand if necessary.
        Args:
            id : int
                New device ID
        Returns:
            None
        """
        self._id = id

    @property
    def origin(self) -> int:
        return self._origin

    @origin.setter
    def origin(self, origin):
        self._origin = origin

    @property
    def destination(self) -> int:
        return self._destination

    @destination.setter
    def destination(self, destination):
        self._destination = destination

    @property
    def bandwidth(self) -> float:
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, bandwidth: float):
        """
        Sets a Physical Link's Bandwidth (in kBytes/s)

        Args:
            bandwidth : float
                Physical link's bandwidth (in kBytes/s)
        """
        self._bandwidth = bandwidth
        try:
            self.metric = self.metric_type(bandwidth, self.distance, self.delay) # type:ignore
        except AttributeError:
            pass
        except:
            raise


    @property
    def delay(self) -> float:
        return self._delay

    @delay.setter
    def delay(self, delay:float):
        """
        Sets a Physical Link's associated delay

        Args:
            delay : float
                Physical link's delay
        """
        self._delay = delay
        try:
            self.metric = self.metric_type(self.bandwidth, self.distance, delay) # type:ignore
        except AttributeError:
            pass
        except:
            raise


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
        if self.origin == device_1_id and self.destination == device_2_id:
            return True
        return False
