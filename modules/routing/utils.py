# from ..resource import PhysicalNetwork

# import networkx as nx

# def find_shortest_path(physical_network: PhysicalNetwork, source_id: int, target_id: int):
#     graph = physical_network.extract_networkx_graph()
#     # Assuming the graph is weighted, if not, weights need to be added
#     shortest_path = nx.dijkstra_path(graph, source=source_id, target=target_id, weight='bandwidth')  # or weight='bandwidth'
#     return shortest_path


# def find_k_shortest_paths(physical_network: PhysicalNetwork, source_id: int, target_id: int, k: int):
#     graph = physical_network.extract_networkx_graph()
#     paths = list(nx.shortest_simple_paths(graph, source=source_id, target=target_id, weight='latency'))[:k]
#     return paths


# def update_routes_for_destination(self, source, destination):
#         # Extract the current network graph from PhysicalNetwork
#         graph = self.physical_network.extract_network_graph()

#         # Compute the shortest path from source to destination
#         try:
#             path = nx.dijkstra_path(graph, source=source, target=destination, weight='weight')
#             cost = nx.dijkstra_path_length(graph, source=source, target=destination, weight='weight')
#         except nx.NetworkXNoPath:
#             print(f"No path between {source} and {destination}.")
#             return

#         # Create a LinkMetric object based on the computed cost (or other criteria)
#         metric = LinkMetric(cost=cost)

#         # Update or add the route for the destination
#         route = Route(destination=destination, metric=metric, path=path)
#         self.routes[destination] = route  # Assuming one best route per destination for simplicity

#     def compute_all_routes(self):
#         # Assuming there's a way to list all nodes or destinations in the graph
#         all_nodes = self.physical_network.get_all_nodes()
#         for destination in all_nodes:
#             self.update_routes_for_destination(self.physical_network.source_router_id, destination)