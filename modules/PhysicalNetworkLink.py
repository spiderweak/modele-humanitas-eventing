"""
Physical Network Link module, defines the physical link constraints and capabilities for inter-devices links

Usage:

"""

class PhysicalNetworkLink:
    # A PhysicalNetworkLink is defined as a link between two physical devices

    # A Physical Network Link is plugged on two network interfaces (Will need to modify device description)

    # For now, the Physical Link is plugged between two devices in a directional way, device IDs are not swappable
    id = 0


    @classmethod
    def _generate_id(cls):
        """
        Class method for id generation
        Assigns id then increment for next generation

        Args:
            None

        Returns:
            result : int, Device ID
        """
        result = cls.id
        cls.id +=1
        return result


    def __init__(self, device_1_id=-1, device_2_id=-1) -> None:
        """
        Initializes the device with basic values
        Assigns ID, initial position, resource values, routing table and resource limits

        Args:
            None

        Returns:
            None
        """
        # ID setting
        self.id = PhysicalNetworkLink._generate_id()
        self.device_1_id = device_1_id
        self.device_2_id = device_2_id

        self.bandwidth = 1000 * 1024 # Bandwidth in KB/s
        self.latency = 10 # Additionnal Latency, defined when creating the link, needs to be defined as a distance function
        self.bandwidth_use = 0


    def setLinkID(self, id):
        """
        Sets a Physical Link's ID by hand if necessary

        Args:
            id : int, new device ID

        Returns:
            None
        """
        self.id = id


    def setPhysicalNetworkLinkBandwidth(self, bandwidth):
        """
        Sets a Physical Link's Bandwidth (in kBytes/s)

        Args:
            bandwidth : float, physical link's bandwidth (in kBytes/s)

        Returns:
            None
        """
        self.bandwidth = bandwidth


    def setPhysicalNetworkLinkLatency(self, latency):
        """
        Sets a Physical Link's associated latency

        Args:
            latency : float, physical link's latency

        Returns:
            None
        """
        self.latency = latency


    def getPhysicalNetworkLinkLatency(self):
        """
        Returns the Physical Link's associated latency

        Args:
            None

        Returns:
            latency : float, physical link's latency
        """
        return self.latency


    def availableBandwidth(self):
        """
        Returns the Physical Link's available (unused) bandwidth (in kBytes/s)

        Args:
            None

        Returns:
            available_bandwidth : float, physical link's available bandwidth
        """
        available_bandwidth = self.bandwidth - self.bandwidth_use
        return available_bandwidth


    def useBandwidth(self, bandwidth_request):
        """
        Allocates Physical Link's bandwidth based on bandwidth request (in kBytes/s)

        Args:
            bandwidth_request : float, necessary bandwidth to allocate (in kBytes/s)

        Returns:
            Boolean, True if allocation possible and successfull, else False
        """
        if bandwidth_request < self.availableBandwidth():
            self.bandwidth_use += bandwidth_request
            return True
        else:
            return False

    def freeBandwidth(self, free_bandwidth_request):
        """
        Free a part of the Physical Link's bandwidth based on free bandwidth request (in kBytes/s)
        If requested bandwidth is superior to allocated bandwidth, bandwidth use is set to 0 instead of negative value

        Args:
            free_bandwidth_request : float, necessary bandwidth to free (in kBytes/s)

        Returns:
            None
        """
        self.bandwidth_use = max(self.bandwidth_use-free_bandwidth_request, 0)

    def checkPhysicalLink(self, device_1_id, device_2_id):
        """
        Check if the associated link actually links the two given devices

        Args:
            free_bandwidth_request : float, necessary bandwidth to free (in kBytes/s)

        Returns:
            None
        """
        if self.device_1_id == device_1_id and self.device_2_id == device_2_id:
            return True
        return False
