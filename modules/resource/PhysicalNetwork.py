import json
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.ResourceManagement import custom_distance
import numpy as np
"""
Physical Network Link module, defines the physical link constraints and capabilities for inter-devices links

Usage:

"""

class PhysicalNetwork:


    def __init__(self, size = 1) -> None:

        self.links = np.array([[None] * size] * size)

        # Links need to be a matrix of Physical Network Links


    def selectLink(self, source_id, destination_id):

        physical_links = []

        for link in self.links:
            if link.checkPhysicalLink(source_id, destination_id):
                physical_links.append(link)


    def addLink(self, physical_network_link):

        origin_device_id = physical_network_link.getOrigin()
        destination_device_id = physical_network_link.getDestination()

        self.links[origin_device_id][destination_device_id] = physical_network_link


    def generatePhysicalNetwork(self):
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
                device_1_id = device_1.getDeviceID()
                for device_2 in env.getDevices():
                    device_2_id = device_2.getDeviceID()
                    distance = custom_distance(device_1.position.values(),device_2.position.values())
                    new_physical_network_link_id = device_1_id*number_of_devices + device_2_id
                    if distance < env.config.wifi_range:
                        device_1.addToRoutingTable(device_2_id, device_2_id, distance)
                        device_2.addToRoutingTable(device_1_id, device_1_id, distance)
                        new_physical_network_link = PhysicalNetworkLink(device_1_id, device_2_id)
                        new_physical_network_link.setLinkID(new_physical_network_link_id)
                        if device_1_id == device_2_id:
                            new_physical_network_link.setPhysicalNetworkLinkLatency(0)
                        env.physical_network_links[new_physical_network_link_id] = new_physical_network_link
                        link = {"source": device_1_id, "target": device_2_id, "weight": distance, "id": new_physical_network_link_id}
                        env.devices_links.append(link)
                    else:
                        new_physical_network_link = PhysicalNetworkLink()
                        env.physical_network_links[new_physical_network_link_id] = None
        """
        raise NotImplementedError

    def extractNetworkMatrix(self, filename = None):
        export_arr = np.empty(self.links.shape, dtype=int)

        for index, link in np.ndenumerate(self.links):
            if link is None:
                export_arr[index] = 0
            else:
                export_arr[index] = 1

        if filename:
            np.savetxt(filename, export_arr, fmt='%d', delimiter=',')
        return export_arr


    def extractLatencyMatrix(self, filename = None):
        export_arr = np.empty(self.links.shape, dtype=int)

        for index, link in np.ndenumerate(self.links):
            if link is None:
                export_arr[index] = -1
            else:
                export_arr[index] = link.latency

        if filename:
            np.savetxt(filename, export_arr, fmt='%.2f', delimiter=',')
        return export_arr


    def extractBandwidthMatrix(self, filename = None):
        export_arr = np.empty(self.links.shape, dtype=int)

        for index, link in np.ndenumerate(self.links):
            if link is None:
                export_arr[index] = -1
            else:
                export_arr[index] = link.bandwidth

        if filename:
            np.savetxt(filename, export_arr, fmt='%.2f', delimiter=',')
        return export_arr


    def extractAvailableBandwidthMatrix(self, filename = None):
        export_arr = np.empty(self.links.shape, dtype=int)

        for index, link in np.ndenumerate(self.links):
            if link is None:
                export_arr[index] = -1
            else:
                export_arr[index] = link.bandwidth - link.bandwidth_use

        if filename:
            np.savetxt(filename, export_arr, fmt='%.2f', delimiter=',')
        return export_arr