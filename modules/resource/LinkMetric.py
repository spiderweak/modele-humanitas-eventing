
from abc import ABC, abstractmethod
import math

OSPF_REFERENCE_BANDWIDTH = 1000 # Mb/s
DEFAULT_WIFI_RANGE = 6

class LinkMetric(ABC):
    def __init__(self, bandwidth: float, distance: float = 0, delay: float = 0):
        """
        Bandwidth in Mb/s
        """
        self.delay = delay
        self.bandwidth = bandwidth
        self.distance = distance
        self.total = self.calculate_total()

    def __lt__(self, other) -> bool:
        return self.total < other.total

    def __eq__(self, other) -> bool:
        return self.total == other.total

    @abstractmethod
    def __add__(self, other):
        pass

    def __radd__(self, other):
        return other.__add__(self)

    @abstractmethod
    def calculate_total(self) -> float:
        pass


class OSPFLinkMetric (LinkMetric):
    def __init__(self, bandwidth: float, distance: float = 0, delay: float = 0):
        super().__init__(bandwidth, distance, delay)

    def calculate_total(self) -> float:
        # Route Metric will be computed as follow :
        # Default value is OSPF Metric with a reference value of 1024 Mb/s, adjusted with delay and distance
        # Default delay value is 0, I advise to pick values less than 1 to keep bandwidth the main discriminant
        # Distance would probably be better as distance / MAX_RANGE to normalize between 0 and 1
        if self.bandwidth == math.inf:
            return 0

        return max(1, OSPF_REFERENCE_BANDWIDTH / self.bandwidth) + self.distance/DEFAULT_WIFI_RANGE + self.delay

    def __add__(self, other):
        if isinstance(other, float) or isinstance(other, int):
            return self.total + other

        if isinstance(other, LinkMetric):
            return self.total + other.total

        if other is None:
            return self.total
