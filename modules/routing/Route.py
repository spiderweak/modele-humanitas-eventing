from typing import List, Dict

class Route:
    def __init__(self, next_hop: int, metric: float, path: List[int]):
        """
        Route definition

        Args:
            next_hop : int ID of the next hop toward destination
            metric: A dictionary holding metrics like delay, bandwidth, distance, etc.
            path : The entire path as a list of device IDs
        """
        self.next_hop = next_hop
        self.metric = metric
        self.path = path

    def __lt__(self, other):
        return self.metric < other.metric
