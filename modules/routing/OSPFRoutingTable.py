from typing import Dict, List

from modules.routing.Route import Route, route_generation
from modules.routing.RoutingTable import RoutingTable

import bisect

class OSPFRoutingTable(RoutingTable):
    
    def __init__(self, device: Device, physical_network : PhysicalNetwork):
        self.physical_network = physical_network
        self.device = device
        self.routes : Dict[Device,List[Route]]= {} # type:ignore  # noqa: F821
        # Maps destinations to Route objects

    def append_neighboring_routes(self, k_param:int = -1) -> bool:
        change = False
        for device, physical_link in self.device.neighboring_devices.items():
            if device.ospf_routing_table is not None:
                for destination_device, destination_device_routes in device.ospf_routing_table.routes.items():
                    for destination_device_route in destination_device_routes:
                        new_route = route_generation(physical_link, destination_device_route)
                        if destination_device not in self.routes:
                            self.routes[destination_device] = []
                        if new_route not in self.routes[destination_device]:
                            bisect.insort(self.routes[destination_device], new_route)
                            if new_route in self.routes[destination_device][:k_param]:
                                change = True

        return change

    def add_route(self, destination: Device, route: Route):
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

    def remove_route(self, destination: Device, route: Route):
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


    def find_k_shortest_paths(self, destination: Device, k: int = 20) -> List[Route]:
        return sorted(self.routes[destination], key=lambda route: route.metric)[:k]