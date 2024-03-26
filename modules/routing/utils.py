from ..resource import PhysicalNetwork

import networkx as nx

def find_shortest_path(physical_network: PhysicalNetwork, source_id: int, target_id: int):
    graph = physical_network.extract_networkx_graph()
    # Assuming the graph is weighted, if not, weights need to be added
    shortest_path = nx.dijkstra_path(graph, source=source_id, target=target_id, weight='bandwidth')  # or weight='bandwidth'
    return shortest_path


def find_k_shortest_paths(physical_network: PhysicalNetwork, source_id: int, target_id: int, k: int):
    graph = physical_network.extract_networkx_graph()
    paths = list(nx.shortest_simple_paths(graph, source=source_id, target=target_id, weight='latency'))[:k]
    return paths
