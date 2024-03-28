
from abc import ABC, abstractmethod

OSPF_REFERENCE_BANDWIDTH = 1024 # Mb/s


class LinkMetric(ABC):
    def __init__(self, bandwidth: float, distance: float = 0, delay: float = 0, arbitrary_delay: float = 0):
        """
        Bandwidth in Mb/s
        """
        self.delay = delay
        self.bandwidth = bandwidth
        self.distance = distance
        self.arbitrary_delay = arbitrary_delay
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
    def __init__(self, bandwidth: float, distance: float = 0, delay: float = 0, arbitrary_delay: float = 0):
        super().__init__(bandwidth, distance, delay, arbitrary_delay)

    def calculate_total(self) -> float:
        # Route Metric will be computed as follow :
        # Default value is OSPF Metric with a reference value of 1024 Mb/s, adjusted with delay and distance
        # Default delay value is 0, I advise to pick values less than 1 to keep bandwidth the main discriminant
        # Distance would probably be better as distance / MAX_RANGE to normalize between 0 and 1
        return max(1, OSPF_REFERENCE_BANDWIDTH / self.bandwidth) + self.delay + self.distance + self.arbitrary_delay

    def __add__(self, other):
        if other.isinstance(int):
            return OSPFLinkMetric(self.bandwidth, self.distance, self.delay, self.arbitrary_delay + other)

        if other.isinstance(LinkMetric):
            return OSPFLinkMetric(min(self.bandwidth, other.bandwidth),
                                  self.distance + other.distance,
                                  self.delay + other.delay,
                                  self.arbitrary_delay + other.arbitrary_delay)
