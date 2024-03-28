from typing import Dict, List

from modules.routing.Route import Route, route_generation
from modules.routing.RoutingTable import RoutingTable
from modules.resource.PhysicalNetworkLink import LinkMetric

import bisect
import time
class OSPFRoutingTable(RoutingTable):
    def __init__(self, device, physical_network):
        self.physical_network = physical_network
        self.device = device
        self.routes : Dict[Device,List[Route]]= {} # type:ignore  # noqa: F821
        # Maps destinations to Route objects


    def initialize_routing_table_content(self):
        for device, physical_link in self.device.neighboring_devices.items():
            new_route = route_generation(physical_link, None)
            if device not in self.routes:
                self.routes[device] = []
            if new_route not in self.routes[device] and new_route.destination != self.device.id:
                bisect.insort(self.routes[device], new_route)

    def append_neighboring_routes(self, k_param:int = -1) -> bool:
        change = False
        for device, physical_link in self.device.neighboring_devices.items():
            if device.ospf_routing_table is not None:
                if self.device.id != device.id:
                    for destination_device, destination_device_routes in device.ospf_routing_table.routes.items():
                        if self.device.id != destination_device.id:
                            for destination_device_route in destination_device_routes:
                                new_route = route_generation(physical_link, destination_device_route)
                                if destination_device not in self.routes:
                                    self.routes[destination_device] = []
                                if new_route not in self.routes[destination_device]:
                                    bisect.insort(self.routes[destination_device], new_route)
                                    if new_route in self.routes[destination_device][:k_param]:
                                        change = True
        return change

    def add_route(self, destination, route: Route):
        if destination not in self.routes:
            self.routes[destination] = []

        # Attempt to find an existing route with the same path
        for existing_route in self.routes[destination]:
            if existing_route.path == route.path:
                # If an existing route is found, compare metrics
                if existing_route.metric != route.metric:
                    # Update the route metric if different
                    existing_route.metric = route.metric
                return  # Exit as the route exists and is updated if necessary

        # If no existing route is found, add the new route
        bisect.insort(self.routes[destination], route)

    def remove_route(self, destination, route: Route):
        try:
            if destination in self.routes:
                if route in self.routes[destination]:
                    self.routes[destination].remove(route)
        except:
            pass

    def find_best_route(self, destination):
        if destination in self.routes:
            return min(self.routes[destination], key=lambda route: route.metric)
        return None

    def find_k_shortest_paths(self, destination, k: int = 20) -> List[Route]:
        return sorted(self.routes[destination], key=lambda route: route.metric)[:k]

    def content(self):
        data = {}
        for device, routes in self.routes.items():
            data[device.id] = []
            for route in routes[:2]:
                destination = route.destination
                if isinstance(route.metric, LinkMetric):
                    metric = route.metric.total
                else:
                    metric = route.metric
                data[device.id].append((destination, metric))
        return data