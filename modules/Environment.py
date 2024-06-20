"""
Environment Module

This module defines the Environment class, which represents the environment for the network simulation.
It includes methods for managing devices, applications, physical network links, and resource usage.

Classes:
    Environment: Represents the environment for the network simulation.

Usage Example:
    env = Environment()
    env.config = Config()
    env.generate_device_list()
    env.generate_application_list()
    env.simulate()
"""

import logging
import json
from tqdm import tqdm
import random
import networkx as nx
import os
import matplotlib.pyplot as plt
import numpy as np
import math
import time
import datetime
from typing import List, Dict, Optional, Union

from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink, OSPFLinkMetric
from modules.resource.Application import Application
from modules.resource.Device import Device
from modules.resource.PhysicalNetwork import PhysicalNetwork
from modules.resource.Data import Data
from modules.Config import Config
from modules.CustomExceptions import (NoRouteToHost, DeviceNotFoundError, ApplicationNotFoundError)
from modules.ResourceManagement import custom_distance
from modules.routing.OSPFRoutingTable import OSPFRoutingTable

class Environment(object):
    """
    Represents the environment for the network simulation.

    The `Environment` class primarily acts as a structure for storing
    information about various network elements like configuration, device info,
    application info, network links, etc.

    Attributes:
        current_time (int): The date and time of the current event.
        config (Config): Environment configuration.
        devices (List[Device]): List of Device objects.
        applications (List[Application]): List of Application objects to be deployed.
        physical_network_links (List[PhysicalNetworkLink]): List of physical network links between devices.
        count_rejected_application (List[List[int]]): Count of rejected applications by time and reason.
        count_accepted_application (List[List[int]]): Count of accepted applications by time.
        list_accepted_application (List[int]): List of accepted applications.
        count_tentatives (List[List[int]]): Count of placement tentatives with success.
        rejected_application_by_reason (Dict): Reasons for application rejection.
        list_devices_data (Optional[Dict]): Data about devices (optional).
        list_currently_deployed_app_data (Optional[List]): Currently deployed applications data (optional).
        data (Data): Data object for the environment.
    """

    TIME_PERIOD = 24 * 60 * 60 * 100


    def __init__(self):
        """
        Initializes the `Environment` class to empty lists, None or 0 values.
        """
        self.current_time: int = 0
        self.config = None
        self.currently_deployed_apps: List[Application] = []
        self.devices = []
        self.id_to_device: Dict[int, Union[None, Device, List[Device]]] = {}
        self.applications = []
        self.id_to_application: Dict[int, Union[None, Application, List[Application]]] = {}
        self.devices_links: List[Dict[str, int]] = []
        self.physical_network: PhysicalNetwork = PhysicalNetwork()
        self.count_rejected_application: List[List[int]] = [[0, 0]]
        self.count_accepted_application: List[List[int]] = [[0, 0]]
        self.list_accepted_application: List[int] = []
        self.count_tentatives: List[List[int]] = [[0, 0]]
        self.rejected_application_by_reason = dict()
        self.list_devices_data: Optional[Dict] = None
        self.list_currently_deployed_app_data: Optional[List] = None
        self.data = Data()
        self.data_folder = "."


    @property
    def config(self) -> Optional[Config]:
        """
        Get the Config object for the environment.

        :return: The Config object, or None if not set.
        :rtype: Optional[Config]
        """
        return self._config

    @config.setter
    def config(self, config: Optional[Config]) -> None:
        """
        Sets the configuration based on a given instantiated `Config` class.

        :param config: Environment configuration generated in the `Config` module.
        :type config: Optional[Config]
        """
        self._config = config

    @property
    def devices(self) -> List[Device]:
        """
        Get the list of Device objects in the environment.

        :return: The list of Device objects representing network devices.
        :rtype: List[Device]
        """
        return self._devices

    @devices.setter
    def devices(self, devices: List[Device]) -> None:
        """
        Set the list of Device objects for the environment.

        :param devices: A list of Device objects to represent network devices in the environment.
        :type devices: List[Device]
        """
        self._devices = []
        self.id_to_device = {}
        for device in devices:
            self.add_device(device)

    def add_device(self, device: Device) -> None:
        """
        Adds a new `Device` to the devices list.

        The id_to_device dictionary is updated along the way. We use a trick so that dictionary members are either a single device or a list.

        :param device: The `Device` object to be added.
        :type device: Device
        """
        self._devices.append(device)
        existing_device = self.id_to_device.get(device.id)

        if existing_device is None:
            self.id_to_device[device.id] = device
        elif isinstance(existing_device, list):
            existing_device.append(device)
        else:
            self.id_to_device[device.id] = [existing_device, device]

    def remove_device(self, device: Device) -> None:
        """
        Removes a `Device` from the devices list

        :param device: The `Device` object to be added.
        :type device: Device
        """
        try:
            self._devices.remove(device)
            existing_device = self.id_to_device.get(device.id)

            if isinstance(existing_device, list):
                existing_device.remove(device)
                if len(existing_device) == 1:
                    self.id_to_device[device.id] = existing_device[0]
            else:
                del self.id_to_device[device.id]
        except ValueError:
            raise DeviceNotFoundError("Device not found in the list.")

    def get_device_by_id(self, dev_id: int) -> Device:
        """
        Gets the `Device` whose ID matches `dev_id`.

        `Device` IDs are supposed to be unique by construction.

        :param dev_id: Device identifier.
        :type dev_id: int
        :return: The device with the matching ID.
        :rtype: Device
        :raises DeviceNotFoundError: If no device is found.
        """
        device = self.id_to_device.get(dev_id)
        if device is None:
            raise DeviceNotFoundError
        if isinstance(device, list):
            return device[0]
        return device

    def get_random_device(self) -> Device:
        """
        Get a random `Device` from the list of devices.

        :return: A random `Device` object.
        :rtype: Device
        :raises DeviceNotFoundError: If no devices are available.
        """
        if not self.devices:
            raise DeviceNotFoundError("No devices are available.")
        return random.choice(self.devices)

    def generate_device_list(self) -> None:
        """
        Generates the list of devices from the configuration file.

        :raises ValueError: If Config is not initialized.
        """
        if self.config is None:
            raise ValueError("Config is not initialized.")

        with open(self.config.devices_file) as file:
            json_data = json.load(file)

        try:
            for device in json_data['devices']:
                dev = Device(data=device, routing_table_type=OSPFRoutingTable)
                self.add_device(dev)
        except KeyError:
            n_devices = self.config.number_of_devices # Number of devices
            try:
                with open(self.config.devices_file) as devices_template_file:
                    devices_data = json.load(devices_template_file)
                    for device_data in devices_data['devices']:
                        device = {}
                        device['id'] = device_data['id']
                        device['position'] = dict()
                        device['position']['x'] = device_data['x']
                        device['position']['y'] = device_data['y']
                        device['position']['z'] = device_data['z']
                        device['resource'] = {"cpu": 8, "gpu": 8, "mem": 8192, "disk": 1024000}
                        dev = Device(data=device, routing_table_type=OSPFRoutingTable)
                        self.add_device(dev)
            except FileNotFoundError:
                for dev_id in range(n_devices):
                    # Processing device position, random x, y, z fixed to between various values (z=0 for now)
                    device = {}
                    device['id'] = dev_id
                    device['position'] = dict()
                    device['position']['x'] = round(random.random() * (self.config._3D_space['x_max'] - self.config._3D_space['x_min']) + self.config._3D_space['x_min'], 2)
                    device['position']['y'] = round(random.random() * (self.config._3D_space['y_max'] - self.config._3D_space['y_min']) + self.config._3D_space['y_min'], 2)
                    device['position']['z'] = round(random.random() * (self.config._3D_space['z_max'] - self.config._3D_space['z_min']) + self.config._3D_space['z_min'], 2)
                    device['resource'] = {"cpu": 8, "gpu": 8, "mem": 8192, "disk": 1024000}
                    dev = Device(data=device, routing_table_type=OSPFRoutingTable)
                    self.add_device(dev)

    def set_data_max(self) -> None:
        """
        Set maximum values for each resource in the data object.
        """
        max_data = {}
        for device in self.devices:
            for resource, value in device.resource_limit.items():
                max_data[resource] = max_data.get(resource, 0) + value

        self.data.set_max_values(max_data['cpu'], max_data['gpu'], max_data['mem'], max_data['disk'])

    @property
    def applications(self) -> List[Application]:
        """
        Get the list of Application objects in the environment.

        :return: The list of Application objects representing network applications.
        :rtype: List[Application]
        """
        return self._applications

    @applications.setter
    def applications(self, applications: List[Application]) -> None:
        """
        Set the list of Application objects for the environment.

        :param applications: A list of Application objects to represent network applications in the environment.
        :type applications: List[Application]
        """
        self._applications = []
        self.id_to_application = {}
        for application in applications:
            self.add_application(application)

    def add_application(self, application: Application) -> None:
        """
        Adds a new `Application` to the applications list.

        The id_to_application dictionary is updated as well.

        :param application: The `Application` object to be added.
        :type application: Application
        """
        self._applications.append(application)
        existing_application = self.id_to_application.get(application.id)

        if existing_application is None:
            self.id_to_application[application.id] = application
        elif isinstance(existing_application, list):
            logging.warning("Duplicated Application ID, Carefull with handling this")
            existing_application.append(application)
        else:
            self.id_to_application[application.id] = [existing_application, application]

    def remove_application(self, application: Application) -> None:
        """
        Removes an `Application` from the applications list.

        :param application: The `Application` object to be removed.
        :type application: Application
        """
        try:
            self._applications.remove(application)
            existing_application = self.id_to_application.get(application.id)

            if isinstance(existing_application, list):
                existing_application.remove(application)
                if len(existing_application) == 1:
                    self.id_to_application[application.id] = existing_application[0]
            else:
                del self.id_to_application[application.id]
        except ValueError:
            raise ApplicationNotFoundError("Application not found in the list.")

    def get_application_by_id(self, app_id: int) -> Application:
        """
        Gets the `Application` whose ID matches `app_id`.

        `Application` IDs are supposed to be unique by construction.

        :param app_id: Application identifier.
        :type app_id: int
        :return: The Application object with the matching ID.
        :rtype: Application
        :raises ApplicationNotFoundError: If no application is found.
        """
        application = self.id_to_application.get(app_id)
        if application is None:
            raise ApplicationNotFoundError("Application not found.")
        if isinstance(application, list):
            return application[0]
        return application

    def generate_application_list(self) -> None:
        """
        Generates a list of `Application` objects and appends them to `self.applications`.

        The number of applications to be generated is retrieved from `self.config.number_of_applications`.

        :raises ValueError: If the config is not initialized.
        """
        if self.config is None:
            raise ValueError("Config is not initialized.")

        for i in tqdm(range(self.config.number_of_applications)):
            application = Application()
            application.random_app_init()
            application.id = i

            if self.config.app_duration != 0:
                application.set_app_duration(self.config.app_duration)

            self.add_application(application)

    def generate_routing_table(self) -> None:
        """
        Generates a routing table on each device in `self.devices`.

        The function first lists the neighboring device, then iterate on the list to build a routing table based on shortest distance among links.
        This is brute forcing the shortest path between devices, we can probably create a better algorithm, but this is not the point for now.
        """
        number_of_devices = len(self.devices)

        # We iterate on the matrix:
        changes = True

        # Approximate number of loops
        logging.info("Generating routing table")
        print("Generating Routing Table, (maximal value is arbitrary)")
        progress_bar = tqdm(total=int(number_of_devices * number_of_devices * 1.5))

        while(changes):
            # As long as the values change
            changes = False
            for i in range(number_of_devices):
                for j in range(number_of_devices):
                    device_i = self.get_device_by_id(i)
                    device_j = self.get_device_by_id(j)

                    try:
                        next_hop, distance = device_i.get_route_info(device_j.id)
                    except NoRouteToHost:
                        next_hop, distance = (-1, 1000)

                    nh_array = [next_hop]
                    dist_array = [distance]
                    for k in range(number_of_devices):
                        device_k = self.get_device_by_id(k)
                        try:
                            next_hop_i_k, distance_i_k = device_i.get_route_info(device_k.id)
                        except NoRouteToHost:
                            next_hop_i_k, distance_i_k = (-1, 1000)

                        try:
                            _, distance_k_j = device_k.get_route_info(device_j.id)
                        except NoRouteToHost:
                            distance_k_j = 1000

                        nh_array.append(next_hop_i_k)
                        dist_array.append(distance_i_k + distance_k_j)

                    min_index = dist_array.index(min(dist_array))
                    min_nh = nh_array[min_index]
                    min_array = dist_array[min_index]

                    if min_array < distance:
                        ## If we observe any change, update and break the loop, keep going
                        changes = True
                        progress_bar.update()
                        device_i.add_to_routing_table(device_j.id, min_nh, min_array)

    def generate_other_routing_table(self, k_param: int = -1) -> None:
        """
        Generates a routing table on each device in `self.devices`.

        :param k_param: The k parameter for the routing table algorithm.
        :type k_param: int
        """
        if k_param == -1 and self.config:
            k_param = self.config.k_param

        for device in self.devices:
            device.initialize_routing_table(self.physical_network, k_param)
            if device.ospf_routing_table is not None:
                device.ospf_routing_table.initialize_routing_table_content()

        ## We iterate on the matrix:

        changes = True
        loop = 0
        # Approximate number of loops
        logging.info("Generating routing table")
        print("Generating Routing Table")

        tst = time.time()
        while(changes):
            st = time.time()

            loop += 1
            # As long as the values change
            changes = False
            count = 0
            for device in self.devices:
                if device.ospf_routing_table is None:
                    raise ValueError("Initialization error")
                output = False
                output = device.ospf_routing_table.append_neighboring_routes()
                changes = changes or output
                count += 1 if output else 0
            et = time.time()
            logging.debug(f"Loop count : {loop}, Loop duration : {str(datetime.timedelta(seconds=et-st))}, Duration from start {str(datetime.timedelta(seconds=et-tst))}, Number of RT modified this round : {count}")
            print(f"Loop count : {loop}, Loop duration : {str(datetime.timedelta(seconds=et-st))}, Duration from start {str(datetime.timedelta(seconds=et-tst))}, Number of RT modified this round : {count}")

    def export_devices(self, filename: str = "devices.json") -> None:
        """
        Export the devices list to a JSON file.

        :param filename: The name of the file to export the devices list to.
        :type filename: str
        """
        output_string = {"devices" : self.devices, "links" : self.devices_links}
        json_string = json.dumps(output_string, default=lambda o: o.__json__(), indent=4)

        with open(filename, 'w') as file:
            file.write(json_string)

    def export_applications(self, filename: str = "applications.json") -> None:
        """
        Export the applications list to a JSON file.

        :param filename: The name of the file to export the applications list to.
        :type filename: str
        """
        json_string = json.dumps(self.applications, default=lambda o: o.__json__(), indent=4)
        with open(filename, 'w') as file:
            file.write(json_string)

    def import_devices(self) -> None:
        """
        Import the devices list from a configuration file.

        :raises ValueError: If the config is not initialized.
        :raises ImportError: If no device list to process.
        """
        if self.config is None:
            raise ValueError("Config is not initialized.")

        if self.config.devices_file is None:
            raise ImportError("No device list to process")

        try:
            with open(self.config.devices_file) as file:
                devices_list = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Please add devices list in argument, default value is devices.json in current directory")

        for device in devices_list['devices']:
            dev = Device(data=device, routing_table_type=OSPFRoutingTable)
            self.add_device(dev)

    def import_ospf_routing_table(self) -> None:
        """
        Import the OSPF routing table from a configuration file.

        :raises ValueError: If the config is not initialized.
        :raises ImportError: If no device list to process.
        """
        if self.config is None:
            raise ValueError("Config is not initialized.")

        if self.config.devices_file is None:
            raise ImportError("No device list to process")

        try:
            with open(self.config.devices_file) as file:
                devices_list = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Please add devices list in argument, default value is devices.json in current directory")

        # Exporting placements list
        print("Importing routing tables")
        logging.info(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Importing routing tables")

        for device_data in tqdm(devices_list['devices']):
            device_id = device_data.get('id')
            device_routing_table = device_data.get('routing_table')
            device = self.get_device_by_id(device_id)
            device.initialize_routing_table(self.physical_network, self.config.k_param)

            if device.ospf_routing_table is not None:
                device.ospf_routing_table.initialize_routing_table_content()
            device.initialize_routing_table_from_dict(self, device_routing_table)

    def import_applications(self) -> None:
        """
        Import the applications list from a configuration file.

        :raises ValueError: If the config is not initialized.
        :raises ImportError: If no application list to process.
        """
        if self.config is None:
            raise ValueError("Config is not initialized.")

        if self.config.applications_file is None:
            raise ImportError("No application list to process")

        try:
            with open(self.config.applications_file) as file:
                applications_list = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Please add application list in argument, default value is applications.json in current directory")
        except json.decoder.JSONDecodeError:
            raise

        for application in applications_list:
            self.add_application(Application(data=application))

    def import_links(self) -> None:
        """
        Import the physical network links from the configuration file.

        :raises ValueError: If the config is not initialized.
        """
        if self.config is None:
            raise ValueError("Config is not initialized.")

        with open(self.config.devices_file) as file:
            json_data = json.load(file)

        try:
            number_of_devices = len(self.devices)
            if (self.config.number_of_devices != number_of_devices):
                print("Discrepency between number of devices in config and in json, will use number of devices in json")
                logging.info("Discrepency between number of devices in config and in json, will use number of devices in json")

            self.physical_network = PhysicalNetwork(size=number_of_devices)
        except:
            raise ImportError
        try:
            for link in json_data['links']:
                self.devices_links.append(link)
                source_device = self.get_device_by_id(int(link['source'])) # Error here, TODO: Better handling of ids types
                target_device = self.get_device_by_id(int(link['target'])) # Error here, TODO: Better handling of ids types

                try:
                    distance = float(link['weight'])
                except KeyError as ke:
                    distance = custom_distance(source_device.position.values(),target_device.position.values())

                source_device.add_to_routing_table(target_device.id, target_device.id, distance)
                # target_device.add_to_routing_table(source_device.id, source_device.id,link['weight'])

                new_physical_network_link = PhysicalNetworkLink(OSPFLinkMetric, source_device.id, target_device.id, size=number_of_devices, distance=distance)

                if source_device.id == target_device.id:
                    new_physical_network_link.delay = 0
                    new_physical_network_link.bandwidth = math.inf

                source_device.neighboring_devices[target_device] = new_physical_network_link

                try:
                    if link['id'] != new_physical_network_link.id:
                        new_physical_network_link.id = int(link['id'])
                except KeyError as ke:
                    pass
                self.physical_network.add_link(new_physical_network_link)

        except KeyError as ke:
            if ke.args[0] == 'links':
                for device_1 in self.devices:
                    device_1_id = device_1.id
                    for device_2 in self.devices:
                        device_2_id = device_2.id
                        distance = custom_distance(device_1.position.values(),device_2.position.values())

                        if distance < self.config.wifi_range:
                            device_1.add_to_routing_table(device_2_id, device_2_id, distance)
                            device_2.add_to_routing_table(device_1_id, device_1_id, distance)

                            new_physical_network_link = PhysicalNetworkLink(OSPFLinkMetric,device_1_id, device_2_id, size=number_of_devices, distance=distance)
                            if device_1_id == device_2_id:
                                new_physical_network_link.delay = 0

                            self.physical_network.add_link(new_physical_network_link)

                            device_1.neighboring_devices[device_2] = new_physical_network_link

                            link = {"source": device_1_id, "target": device_2_id, "weight": distance, "id": new_physical_network_link.id}
                            self.devices_links.append(link)



    def plot_device_network(self) -> None:
        """
        Plot the network of devices.

        Creates a graph of the network and plots it using networkx and matplotlib.
        """
        # Creating a graph
        G = nx.Graph()

        position_list = []
        color_list = []
        # We add the nodes, our devices, to our graph
        for device in self.devices:
            position = [device.position['x'], device.position['y'], device.position['z']]
            G.add_node(device.id, pos=position)
            position_list.append(position)
            color_list.append(device.color)

        # We add the edges, to our graph, which correspond to the wifi reachability

        for link in self.devices_links:
            G.add_edge(link['source'], link['target'])
        # Let's try plotting the network

        # We already have the coords, but let's process it again just to be sure
        x_coords, y_coords, z_coords = zip(*position_list)

        #  We create a 3D scatter plot again
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(projection ='3d')

        # Lets trace the graph by hand
        ## Placing the nodes
        ax.scatter(x_coords, y_coords, z_coords, c=color_list)

        ## Placing the edges by hand
        for i, j in G.edges():
            device_i = self.get_device_by_id(i)
            device_j = self.get_device_by_id(j)
            ax.plot([device_i.position['x'], device_j.position['x']],
                    [device_i.position['y'], device_j.position['y']],
                    [device_i.position['z'], device_j.position['z']],
                    c='lightgray')

        # Set the labels
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlim(0, 50) # type: ignore
        # Title
        ax.set_title(f'Undirected Graph of Devices and links')

        # Saves the graph in a file
        try:
            os.makedirs("fig") # Will need to rework that, but creates a fig folder to host figures
        except FileExistsError:
            pass
        plt.savefig("fig/graph.png")

    def extract_devices_resources(self, resources = ['cpu', 'gpu', 'mem', 'disk'], filename = "devices_data.json") -> Dict:
        """
        Extract the resources of the devices and return as a dictionary.

        :param resources: The list of resources to extract.
        :type resources: list
        :param filename: The filename to save the extracted data to.
        :type filename: str
        :return: The dictionary of extracted resources.
        :rtype: Dict
        """
        extracted_data = dict()
        for resource in resources:
            extracted_data[resource] = np.empty(len(self.devices))
            for device in self.devices:
                extracted_data[resource][device.id] = device.resource_limit[resource]

        if filename:
            json_string = json.dumps(extracted_data, default=lambda o: list(o), indent=4)
            with open(filename, 'w') as file:
                file.write(json_string)

        self.list_devices_data = extracted_data

        return extracted_data

    def extract_decision_weights(self) -> Dict:
        """
        Extracts the decision weights of the devices.

        :return: A dictionary with the decision weights of the devices.
        :rtype: Dict
        """
        extracted_data = dict()

        for device in self.devices:
            extracted_data[device.id] = device.closeness_centrality

        return extracted_data

    def extract_currently_deployed_apps_data(self, resources=['cpu', 'gpu', 'mem', 'disk'], filename="apps_data.json") -> List[Dict]:
        """
        Extracts the currently deployed applications data.

        :param resources: The list of resources to extract.
        :type resources: list
        :param filename: The filename to save the extracted data to.
        :type filename: str
        :return: The list of dictionaries containing the currently deployed applications data.
        :rtype: List[Dict]
        """
        extracted_data = []
        for app in self.currently_deployed_apps:
            app_data = dict()
            for resource in resources:
                app_data[resource] = []
                for proc in app.processus_list:
                    app_data[resource].append(proc.resource_request[resource])
            extracted_data.append(app_data)

        if filename:
            json_string = json.dumps(extracted_data, indent=4)
            with open(filename, 'w') as file:
                file.write(json_string)

        self.list_currently_deployed_app_data = extracted_data

        return extracted_data

    def extract_values(self) -> None:
        """
        Extracts and processes various values from the environment.
        """
        self.physical_network.extract_network_matrix()
        self.extract_devices_resources()


    def import_results(self) -> None:
        """
        Imports the results from the results file.

        :raises ValueError: If the config is not initialized.
        :raises NotImplementedError: If device processing is not implemented.
        """
        if self.config is None:
            raise ValueError("Config is not initialized.")

        with open(self.config.results_filename) as file:
            print(self.config.results_filename)
            json_data = json.load(file)
        try:
            for device in json_data['devices']:
                dev = Device(data=device, routing_table_type=OSPFRoutingTable)
                self.add_device(dev)
        except:
            raise NotImplementedError

    def process_closeness_centrality(self) -> Dict[int, float]:
        """
        Processes the closeness centrality for the physical network and updates devices.

        :return: A dictionary mapping device IDs to their computed closeness centrality values.
        :rtype: Dict[int, float]
        """
        computed_cc = self.physical_network.compute_closeness_centrality()

        for k, v in computed_cc.items():
            device = self.get_device_by_id(k)
            device.closeness_centrality = v

        return computed_cc

    def set_data_folder(self, folder=".") -> None:
        """
        Sets the data folder for the environment.

        :param folder: The path to the data folder.
        :type folder: str
        """
        self.data_folder = folder
