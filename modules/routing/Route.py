from typing import List, Dict
from ..resource import Path
from . import RouteMetric

class Route:
    def __init__(self, destination: int, metric: RouteMetric, path: Path):
        """
        Route definition

        Args:
            destination : int ID of the destination
            metric: A dictionary holding metrics like delay, bandwidth, distance, etc.
            path : The entire path as a list of device IDs
        """
        self.destination = destination
        self.metric = metric
        self.path = path

    def __lt__(self, other):
        return self.metric < other.metric

    def __eq__(self, other):
        return self.metric == other.metric