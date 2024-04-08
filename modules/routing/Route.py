from typing import List, Dict, Optional, Union
from modules.resource.Path import Path
from modules.resource.LinkMetric import LinkMetric, OSPFLinkMetric
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Path import path_append_left

import time

class Route:
    def __init__(self, origin: int, destination: int, metric: Union[LinkMetric, float], path: Path):
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
        if isinstance(other, (float, int)):
            return self.metric < other

        return self.metric < other.metric

    def __eq__(self, other):
        if isinstance(other, (float, int)):
            return False

        if self.destination != other.destination or self.path != other.path:
            return False
        return True

    def __to_self(self, device_id):
        self.origin = device_id
        self.destination = device_id
        self.metric = 0
        self.path = None

    def __json__(self):
        return {
            "origin" : self.origin,
            "destination" : self.destination,
            "metric" : self.metric.total if isinstance(self.metric, LinkMetric) else self.metric,
            "path" : list(self.path.devices_path) if self.path is not None else []
        }

def route_generation(physical_link: PhysicalNetworkLink, route: Optional[Route]) -> Route:
    if route is not None:
        old_path = route.path
        old_metric = route.metric
        destination = route.destination
    else:
        old_path = None
        old_metric = 0.0
        destination = physical_link.destination

    # if route is not None:
    #     print(f"Route from {route.origin}")
    #     print(f"Route to {route.destination}")
    #     print(f"Physical link : {physical_link.origin}, {physical_link.destination}")
    #     print(f"Old path : {old_path.devices_path if old_path is not None else 0}")

    new_path = path_append_left(physical_link, old_path)
    new_route = Route(physical_link.origin, destination, physical_link.metric + old_metric, new_path) # type: ignore

    return new_route