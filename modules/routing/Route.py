from typing import List, Dict
from modules.resource.Path import Path
from modules.resource.LinkMetric import LinkMetric
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Path import path_append_left

class Route:
    def __init__(self, destination: int, metric: LinkMetric, path: Path):
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
        if self.destination != other.destination or self.path != other.path:
            return False
        return True

    def __to_self(self, device_id):
        self.destination = device_id
        self.metric = 0
        self.path = None

def route_generation(physical_link: PhysicalNetworkLink, route: Route) -> Route:
    old_path = route.path
    new_path = path_append_left(physical_link, old_path)
    new_route = Route(route.destination, physical_link.metric + route.metric, new_path) # type:ignore

    return new_route