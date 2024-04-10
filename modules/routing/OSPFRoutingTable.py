from typing import Dict, List

from modules.routing.Route import Route, route_generation
from modules.routing.RoutingTable import RoutingTable
from modules.resource.PhysicalNetworkLink import LinkMetric
from modules.resource.Path import Path

import bisect
import time

class OSPFRoutingTable(RoutingTable):
    def __init__(self, device, physical_network, k_param : int = -1):
        self.physical_network = physical_network
        self.device = device
        self.routes : Dict[Device,List[Route]]= {} # type:ignore  # noqa: F821
        self.routing_table_size_limit = k_param
        # Maps destinations to Route objects

    def __json__(self):
        return {key.id if key is not None else -1: value[:10] for key, value in self.routes.items()}

    def initialize_routing_table_content(self):
        for device, physical_link in self.device.neighboring_devices.items():
            new_route = route_generation(physical_link, None)
            if device not in self.routes:
                self.routes[device] = []
            if new_route not in self.routes[device] and new_route.destination != self.device.id:
                bisect.insort(self.routes[device], new_route)

    def append_neighboring_routes(self) -> bool:
        change = False
        for device, physical_link in self.device.neighboring_devices.items():
            # Get all neighbors and their associated links
            if device.ospf_routing_table is not None:
                # Ignore empty routing tables in neighbors
                if self.device.id != device.id:
                    # Self can appear in neighbor list, ignore self
                    for destination_device, destination_device_routes in device.ospf_routing_table.routes.items():
                        # Get all routes announced by neighbors
                        if self.device.id != destination_device.id:
                            # Ignore routes to ourselves (prevents loops)
                            for destination_device_route in destination_device_routes:
                                # Get all routes one by one
                                if self.device.id not in destination_device_route.path.devices_path:
                                    # Ignore routes that countain ourselves (prevents loops)
                                    new_route = route_generation(physical_link, destination_device_route)
                                    # Generate a new route from announcement, appends the link from self to neighbor to their announced route to third party
                                    if destination_device not in self.routes:
                                        # Previous destination unknown, creates entry in dictionary
                                        self.routes[destination_device] = []
                                    if new_route not in self.routes[destination_device]:
                                        # Should be tested with route.__eq__ operator, which tests for path __eq__ which tests set equality on devices on the path and links on the path
                                        bisect.insort(self.routes[destination_device], new_route)
                                        # Inserts route based on sorted metric
                                        if new_route in self.routes[destination_device][:self.routing_table_size_limit]:
                                            change = True
                                            # if route appended in the first k, signal updated route
                                        if len(self.routes[destination_device]) >= 5*self.routing_table_size_limit:
                                            # filter to only keep 5k routes
                                            self.routes[destination_device] = self.routes[destination_device][:3*self.routing_table_size_limit]
        return change


    def initialize_routing_table_from_dict(self, env, routing_table_dict):
        for device_id, routes in routing_table_dict.items():
            device = env.get_device_by_id(int(device_id))
            if device not in self.routes:
                self.routes[device] = []
            for route in routes:
                if route:
                    first_device, last_device = route['path'][0], route['path'][-1]
                    new_path = Path(first_device, last_device)
                    new_path.generate_path_from_intermediate_devices(env, route['path'])
                    new_route = Route(route['origin'], route['destination'], route['metric'], new_path)
                if new_route not in self.routes[device] and new_route.destination != self.device.id:
                    bisect.insort(self.routes[device], new_route)


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