from typing import List, Dict, Optional
from modules.resource.Path import Path
from modules.resource.LinkMetric import LinkMetric, OSPFLinkMetric
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Path import path_append_left

import time

class Route:
    def __init__(self, origin: int, destination: int, metric: LinkMetric, path: Path):
        """
        Route definition

        Args:
            destination : int ID of the destination
            metric: A dictionary holding metrics like delay, bandwidth, distance, etc.
            path : The entire path as a list of device IDs
        """
        self.origin = origin
        self.destination = destination
        self.metric = metric
        self.path = path

    def __lt__(self, other):
        return self.metric < other.metric

    def __eq__(self, other):
        if self.destination != other.destination or self.path != other.path:
            return False
        return True

    def __to_self(self, device_id):
        self.origin = device_id
        self.destination = device_id
        self.metric = 0
        self.path = None

def route_generation(physical_link: PhysicalNetworkLink, route: Optional[Route]) -> Route:
    if route is not None:
        old_path = route.path
        old_metric = route.metric
        destination = route.destination
    else:
        old_path = None
        old_metric = 0
        destination = physical_link.destination
    new_path = path_append_left(physical_link, old_path)
    new_route = Route(physical_link.origin, destination, physical_link.metric + old_metric, new_path) # type:ignore

    return new_route