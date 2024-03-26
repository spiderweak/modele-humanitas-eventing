from abc import ABC, abstractmethod

OSPF_REFERENCE_BANDWIDTH = 1024 # Mb/s

class RouteMetric(ABC):
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
    def calculate_total(self) -> float:
        """Add or update a route to a destination."""
        pass


class OSPFRouteMetric (RouteMetric):
    def __init__(self, bandwidth: float, distance: float = 0, delay: float = 0):
        super().__init__(bandwidth, distance, delay)

    def calculate_total(self) -> float:
        # Route Metric will be computed as follow :
        # Default value is OSPF Metric with a reference value of 1024 Mb/s, adjusted with delay and distance
        # Default delay value is 0, I advise to pick values less than 1 to keep bandwidth the main discriminant
        # Distance would probably be better as distance / MAX_RANGE to normalize between 0 and 1
        return min(1, OSPF_REFERENCE_BANDWIDTH / self.bandwidth) + self.delay + self.distance
