"""
Physical Network Link module, defines the physical link constraints and capabilities for inter-devices links

Usage:

"""

import json
import numpy as np
import numpy.typing as npt
import networkx as nx

from typing import List, Tuple, Any
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink, OSPFLinkMetric
from modules.ResourceManagement import custom_distance

class PhysicalNetwork:
    """
    Manages physical network links and provides network matrix extraction methods.

    Attributes:
        links (numpy.array): 2D array holding physical network links between devices.
    """

    def __init__(self, size: int = 1) -> None:
        """
        Initializes a 2D numpy array to store physical network links.

        Args:
            size (int, optional): Size of the 2D array for physical network links. Defaults to 1.
        """

        self.links: npt.NDArray = np.array([[PhysicalNetworkLink(metric_type=OSPFLinkMetric) for _ in range(size)] for _ in range(size)])
        # Links need to be a matrix of Physical Network Links


    def select_link(self, source_id, destination_id):
        """
        Selects a link based on source and destination IDs.

        Args:
            source_id (int): Source device ID.
            destination_id (int): Destination device ID.

        Returns:
            list: List of physical links matching the given source and destination IDs.
        """

        physical_links: List[PhysicalNetworkLink] = []

        for column in self.links:
            for link in column:
                if link.check_physical_link(source_id, destination_id):
                    physical_links.append(link)

        return physical_links


    def add_link(self, physical_network_link: PhysicalNetworkLink) -> None:
        """
        Adds a physical network link to the links 2D array.

        Args:
            physical_network_link (PhysicalNetworkLink): Physical network link object.

        Returns:
            None
        """

        origin_device_id = physical_network_link.origin
        destination_device_id = physical_network_link.destination

        self.links[origin_device_id][destination_device_id] = physical_network_link


    def generate_physical_network(self) -> None:
        """
        Generates physical network links based on a given environment.

        Currently not implemented.

        Returns:
            None
        """
        """
        with open(env.config.devices_template_filename) as file:
            json_data = json.load(file)
        try :
            for link in json_data['links']:
                env.devices_links.append(link)
                source_device = env.getDeviceByID(link['source'])
                target_device = env.getDeviceByID(link['target'])
                source_device.addToRoutingTable(target_device.id, target_device.id,link['weight'])
                target_device.addToRoutingTable(source_device.id, source_device.id,link['weight'])
        except KeyError:

            number_of_devices = len(env.getDevices())

            env.physical_network_links = [0] * number_of_devices * number_of_devices

            for device_1 in env.getDevices():
                device_1_id = device_1.id
                for device_2 in env.getDevices():
                    device_2_id = device_2.id
                    distance = custom_distance(device_1.position.values(),device_2.position.values())
                    new_physical_network_link_id = device_1_id*number_of_devices + device_2_id
                    if distance < env.config.wifi_range:
                        device_1.addToRoutingTable(device_2_id, device_2_id, distance)
                        device_2.addToRoutingTable(device_1_id, device_1_id, distance)
                        new_physical_network_link = PhysicalNetworkLink(OSPFLinkMetric, device_1_id, device_2_id)
                        new_physical_network_link.setLinkID(new_physical_network_link_id)
                        if device_1_id == device_2_id:
                            new_physical_network_link.setPhysicalNetworkLinkDelay(0)
                        env.physical_network_links[new_physical_network_link_id] = new_physical_network_link
                        link = {"source": device_1_id, "target": device_2_id, "weight": distance, "id": new_physical_network_link_id}
                        env.devices_links.append(link)
                    else:
                        new_physical_network_link = PhysicalNetworkLink()
                        env.physical_network_links[new_physical_network_link_id] = None
        """
        raise NotImplementedError


    def extract_network_matrix(self, filename = None) -> npt.NDArray:
        """
        Extracts a binary matrix representing the existence of links.

        Args:
            filename (str, optional): The filename to save the extracted matrix. Defaults to None.

        Returns:
            np.array: Binary matrix representing the existence of links.
        """
        export_arr = np.empty(self.links.shape, dtype=int)

        for index, link in np.ndenumerate(self.links):
            if link is None:
                export_arr[index] = 0
            else:
                export_arr[index] = 1

        if filename:
            np.savetxt(filename, export_arr, fmt='%d', delimiter=',')
        return export_arr


    def extract_delay_matrix(self, filename = None) -> npt.NDArray:
        """
        Extracts a matrix representing the delay of links.

        Args:
            filename (str, optional): The filename to save the extracted matrix. Defaults to None.

        Returns:
            np.array: Matrix representing the delay of links.
        """
        export_arr = np.empty(self.links.shape, dtype=float)

        for index, link in np.ndenumerate(self.links):
            if link is None:
                export_arr[index] = -1
            else:
                export_arr[index] = link.delay

        if filename:
            np.savetxt(filename, export_arr, fmt='%.2f', delimiter=',')
        return export_arr


    def extract_bandwidth_matrix(self, filename = None) -> npt.NDArray:
        """
        Extracts a matrix representing the bandwidth of links.

        Args:
            filename (str, optional): The filename to save the extracted matrix. Defaults to None.

        Returns:
            np.array: Matrix representing the bandwidth of links.
        """
        export_arr = np.empty(self.links.shape, dtype=float)

        for index, link in np.ndenumerate(self.links):
            if link is None:
                export_arr[index] = -1
            else:
                export_arr[index] = link.bandwidth

        if filename:
            np.savetxt(filename, export_arr, fmt='%.2f', delimiter=',')
        return export_arr


    def extract_available_bandwidth_matrix(self, filename = None) -> npt.NDArray:
        """
        Extracts a matrix representing the available bandwidth of links.

        Args:
            filename (str, optional): The filename to save the extracted matrix. Defaults to None.

        Returns:
            np.array: Matrix representing the available bandwidth of links.
        """
        export_arr = np.empty(self.links.shape, dtype=float)

        for index, link in np.ndenumerate(self.links):
            if link is None:
                export_arr[index] = -1
            else:
                export_arr[index] = link.bandwidth - link.bandwidth_use

        if filename:
            np.savetxt(filename, export_arr, fmt='%.2f', delimiter=',')
        return export_arr


    def extract_networkx_graph(self) -> Any:
        nxlinks: List[Tuple[int, int, dict[str, float]]] = []
        for column in self.links:
            for link in column:
                origin = link.origin
                destination = link.destination
                if origin != -1 and destination != -1:
                    nxlinks.append((link.origin, link.destination, {'weight': link.metric.total}))

        return nx.Graph(nxlinks)

    def compute_closeness_centrality(self) -> Any:
        """
        Computes the closeness centrality for the network.

        Currently not implemented.

        Returns:
            None
        """
        extracted_nxgraph = self.extract_networkx_graph()
        cc_dict = nx.closeness_centrality(extracted_nxgraph)
        return cc_dict