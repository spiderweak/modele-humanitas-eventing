from typing import List, Dict, Tuple
from abc import ABC, abstractmethod
from . import Route

class RoutingTable(ABC):
    @abstractmethod
    def add_route(self, destination: int, route: Route):
        """Add or update a route to a destination."""
        pass

    @abstractmethod
    def remove_route(self, destination: int, route: Route):
        """Remove a specific route to a destination."""
        pass

    @abstractmethod
    def find_best_route(self, destination: int) -> Route:
        """Find the best route to a destination."""
        pass

    @abstractmethod
    def find_k_shortest_paths(self, destination: int, k: int = 20) -> List[Route]:
        """Find up to k-shortest paths to a destination."""
        pass
