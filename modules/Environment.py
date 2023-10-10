from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Application import Application
from modules.resource.Device import Device
from modules.resource.PhysicalNetwork import PhysicalNetwork
from modules.Config import Config
from modules.CustomExceptions import (NoRouteToHost, DeviceNotFoundError, ApplicationNotFoundError)
from modules.ResourceManagement import custom_distance

import logging
import json
from tqdm import tqdm
import random
import networkx as nx
import os
import matplotlib.pyplot as plt
import numpy as np

from typing import List, Optional

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
        ...
    """

    TIME_PERIOD: int = 24 * 60 * 60 * 100


    def __init__(self):
        """
        The ``Environment`` class is initialized to empty lists, None or 0 values
        """

        self.current_time: int = 0
        self.config = None

        self.applications: List[Application] = []
        self.currently_deployed_apps: List[Application] = []
        self.devices = []

        self.devices_links: List[dict[str, int]] = []
        self.physical_network: PhysicalNetwork = PhysicalNetwork()

        # Counts the numbers of applications, first value is time, second is value
        self.count_rejected_application: List[List[int]] = [[0, 0]]
        self.count_accepted_application: List[List[int]] = [[0, 0]]
        self.count_tentatives: List[List[int]] = [[0, 0]]

        self.list_devices_data: Optional[dict] = None
        self.list_currently_deployed_app_data: Optional[List] = None


    @property
    def config(self) -> Optional[Config]:
        """Get the Config object for the environment.

        Returns:
            Optional[Config]: The Config object, or None if not set.
        """
        return self._config

    @config.setter
    def config(self, config: Optional[Config]) -> None:
        """Sets the configuration based on a given instanciated `Config` class.

        Args:
            Optional[Config]: Environment configuration generated in the `Config` module
        """
        self._config = config


    @property
    def devices(self) -> List[Device]:
        """Get the list of Device objects in the environment.

        Returns:
            List[Device]: The list of Device objects representing network devices.
        """
        return self._devices

    @devices.setter
    def devices(self, devices: List[Device]):
        """Set the list of Device objects for the environment.

        Args:
            devices (List[Device]): A list of Device objects to represent network devices in the environment.
        """
        self._devices = devices


    def getDeviceByID(self, dev_id: int) -> Device:
        """Gets the `Device` whose ID matches `dev_id`.
        `Device` IDs are supposed to be unique by construction.

        Args:
            dev_id (int): Device identifier.

        Returns:
            Device: The device with the matching ID.
        """
        for device in self.devices:
            if device.id == int(dev_id):
                return device
        raise DeviceNotFoundError


    def getRandomDevice(self) -> Device:
        """Get a random `Device` from the list of devices.

        Returns:
            Optional[Device]: A random `Device` object, or None if no devices are available.

        Raises:
            DeviceNotFoundError: If no devices are available.
        """
        return random.choice(self.devices)


    def addDevice(self, device: Device):
        """Adds a new `Device` to the devices list.

        Args:
            device (Device): The `Device` object to be added.
        """
        self.devices.append(device)


    def getApplicationByID(self, app_id: int) -> Application:
        """Gets the `Application` whose ID matches `app_id`.
        `Application` IDs are supposed to be unique by construction.

        Args:
            app_id (int): Application identifier.

        Returns:
            Optional[Application]: The Application object with the matching ID, or None if not found.

        Raises:
            ApplicationNotFoundError: If no application is found
        """
        for application in self.applications:
            if application.id == app_id:
                return application
        raise ApplicationNotFoundError


    def addApplication(self, application: Application):
        """Adds a new `Application` to the list of applications.

        Args:
            application (Application): The `Application` object to be added.
        """
        self.applications.append(application)


    def removeApplication(self, app_id: int) -> bool:
        """
        Removes the `Application` with the given `app_id` from the list of applications.

        Uses getApplicationByID to locate application to remove.

        `Application` IDs are supposed to be unique, so only one application should be removed.

        Args:
            app_id (int): The ID of the `Application` to be removed.

        Returns:
            bool: True if an application was removed, False otherwise.
        """
        try:
            application_to_remove = self.getApplicationByID(app_id)

        except ApplicationNotFoundError:
            return False

        self.applications.remove(application_to_remove)
        return True


    def generateApplicationList(self) -> None:
        """
        Generates a list of `Application` objects and appends them to `self.applications`.

        The number of applications to be generated is retrieved from `self.config.number_of_applications`.
        """
        if self.config is None:
            raise ValueError("Config is not initialized.")

        for i in tqdm(range(self.config.number_of_applications)):
            application = Application()
            application.randomAppInit()
            application.setAppID(i)

            if self.config.app_duration != 0:
                application.setAppDuration(self.config.app_duration)

            self.applications.append(application)

    # Let's try to code a routing table
    def generateRoutingTable(self):
        """
        Generates a routing table on each device in `self.devices`
        The function first lists the neighboring device, then iterate on the list to build a routing table based on shortest distance among links
        This is bruteforcing the shortest path betweend devices, we can probably create a better algorithm, but this is not the point for now.
        TODO : Fix duplicated entries in routing table
        """

        number_of_devices = len(self.devices)

        ## We iterate on the matrix:

        changes = True

        # Approximative number of loops
        logging.info("Generating routing table")
        print("Generating Routing Table, (maximal value is arbitrary)")
        progress_bar = tqdm(total=int(number_of_devices*number_of_devices*1.5))

        while(changes):
            ## As long as the values change
            changes = False
            for i in range(number_of_devices):
                for j in range(number_of_devices):
                    device_i = self.getDeviceByID(i)
                    device_j = self.getDeviceByID(j)

                    try:
                        next_hop,distance = device_i.getRouteInfo(device_j.id)
                    except NoRouteToHost:
                        next_hop,distance = (-1,1000)

                    nh_array = [next_hop]
                    dist_array = [distance]
                    for k in range(number_of_devices):
                        device_k = self.getDeviceByID(k)
                        try:
                            next_hop_i_k,distance_i_k = device_i.getRouteInfo(device_k.id)
                        except NoRouteToHost:
                            next_hop_i_k,distance_i_k = (-1,1000)

                        try:
                            _,distance_k_j = device_k.getRouteInfo(device_j.id)
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
                        device_i.addToRoutingTable(device_j.id, min_nh, min_array)


    def exportDevices(self, filename = "devices.json"):
        output_string = {"devices" : self.devices, "links" : self.devices_links}
        json_string = json.dumps(output_string, default=lambda o: o.__json__(), indent=4)

        with open(filename, 'w') as file:
            file.write(json_string)


    def exportApplications(self, filename = "applications.json"):
        json_string = json.dumps(self.applications, default=lambda o: o.__json__(), indent=4)
        with open(filename, 'w') as file:
            file.write(json_string)


    def importDevices(self):
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
            dev = Device(data=device)
            self.devices.append(dev)


    def importApplications(self):
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
            self.applications.append(Application(data=application))


    def importLinks(self):
        if self.config is None:
            raise ValueError("Config is not initialized.")

        with open(self.config.devices_template_filename) as file:
            json_data = json.load(file)
        try :

            number_of_devices = len(self.devices)

            if (self.config.number_of_devices != number_of_devices):
                print("Discrepency between number of devices in config and number of device in json, will use number of devices in db")
                logging.info("Discrepency between number of devices in config and number of device in json, will use number of devices in db")

            self.physical_network = PhysicalNetwork(size=number_of_devices)
        except:
            raise ImportError

        try:
            for link in json_data['links']:
                self.devices_links.append(link)
                source_device = self.getDeviceByID(link['source'])
                target_device = self.getDeviceByID(link['target'])
                try:
                    source_device.addToRoutingTable(target_device.id, target_device.id,link['weight'])
                except KeyError as ke:
                    distance = custom_distance(source_device.position.values(),target_device.position.values())
                    source_device.addToRoutingTable(target_device.id, target_device.id,distance)
                # target_device.addToRoutingTable(source_device.id, source_device.id,link['weight'])

                new_physical_network_link = PhysicalNetworkLink(source_device.id, target_device.id, size=number_of_devices)
                try:
                    if link['id'] != new_physical_network_link.id:
                        new_physical_network_link.setLinkID(link['id'])
                except KeyError as ke:
                    pass
                self.physical_network.addLink(new_physical_network_link)

        except KeyError as ke:
            if ke.args[0] == 'links':
                for device_1 in self.devices:
                    device_1_id = device_1.id
                    for device_2 in self.devices:
                        device_2_id = device_2.id
                        distance = custom_distance(device_1.position.values(),device_2.position.values())

                        if distance < self.config.wifi_range:
                            device_1.addToRoutingTable(device_2_id, device_2_id, distance)
                            device_2.addToRoutingTable(device_1_id, device_1_id, distance)

                            new_physical_network_link = PhysicalNetworkLink(device_1_id, device_2_id, size=number_of_devices, latency=distance)
                            if device_1_id == device_2_id:
                                new_physical_network_link.setPhysicalNetworkLinkLatency(0)
                            self.physical_network.addLink(new_physical_network_link)
                            link = {"source": device_1_id, "target": device_2_id, "weight": distance, "id": new_physical_network_link.id}
                            self.devices_links.append(link)


    def generateDeviceList(self):
        if self.config is None:
            raise ValueError("Config is not initialized.")

        with open(self.config.devices_template_filename) as file:
            json_data = json.load(file)

        try:
            for device in json_data['devices']:
                dev = Device(data=device)
                self.devices.append(dev)
        except KeyError:
            n_devices = self.config.number_of_devices # Number of devices
            try:
                with open(self.config.devices_template_filename) as devices_template_file:
                    devices_data = json.load(devices_template_file)
                    for device_data in devices_data['devices']:
                        device = {}
                        device['id'] = device_data['id']
                        device['position'] = dict()
                        device['position']['x'] = device['x']
                        device['position']['y'] = device['y']
                        device['position']['z'] = device['z']
                        device['resource'] = {"cpu": 8, "gpu": 8, "mem": 8192, "disk": 1024000}
            except FileNotFoundError:
                for dev_id in range(n_devices):
                # Processing device position, random x, y, z fixed to between various values (z=0 for now)
                    device = {}
                    device['id'] = dev_id
                    device['position'] = dict()
                    device['position']['x'] = round(random.random() * (self.config._3D_space['x_max'] - self.config._3D_space['x_min']) + self.config._3D_space['x_min'],2)
                    device['position']['y'] = round(random.random() * (self.config._3D_space['y_max'] - self.config._3D_space['y_min']) + self.config._3D_space['y_min'],2)
                    device['position']['z'] = round(random.random() * (self.config._3D_space['z_max'] - self.config._3D_space['z_min']) + self.config._3D_space['z_min'],2)
                    device['resource'] = {"cpu": 8, "gpu": 8, "mem": 8192, "disk": 1024000}


    def plotDeviceNetwork(self):
        # We'll try our hand on plotting everything in a graph

        # Creating a graph
        G = nx.Graph()

        position_list = []
        # We add the nodes, our devices, to our graph
        for device in self.devices:
            position = [device.position['x'], device.position['y'], device.position['z']]
            G.add_node(device.id, pos=position)
            position_list.append(position)

        # We add the edges, to our graph, which correspond to wifi reachability

        for link in self.devices_links:
            G.add_edge(link['source'], link['target'])
        # Let's try plotting the network

        # We alread have the coords, but let's process it again just to be sure
        x_coords, y_coords, z_coords = zip(*position_list)

        #  We create a 3D scatter plot again
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(projection = '3d')

        # Lets trace the graph by hand
        ## Placing the nodes
        ax.scatter(x_coords, y_coords, z_coords, c='b')
        ## Placing the edges by hand
        for i, j in G.edges():
            device_i = self.getDeviceByID(i)
            device_j = self.getDeviceByID(j)
            ax.plot([device_i.position['x'], device_j.position['x']],
                    [device_i.position['y'], device_j.position['y']],
                    [device_i.position['z'], device_j.position['z']], c='lightgray')

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


    def extractDevicesResources(self, resources = ['cpu', 'gpu', 'mem', 'disk'], filename = "devices_data.json"):
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

    def extractDecisionWeights(self):
        extracted_data = dict()

        for device in self.devices:
            extracted_data[device.id] = device.closeness_centrality

        return extracted_data

    def extractCurrentlyDeployedAppData(self, resources = ['cpu', 'gpu', 'mem', 'disk'], filename = "apps_data.json"):
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

        # Generate an array with length equal to number of apps currently deployed
        # Generate an array in this array with length equal to number of procs for each apps
        # Generate a dict with each resource (cpu, gpu, memory, disk) request for each proc for each app
        # return and export to csv

    def extractValues(self):

        self.physical_network.extractNetworkMatrix()
        self.extractDevicesResources()


    def importResults(self):
        if self.config is None:
            raise ValueError("Config is not initialized.")

        with open(self.config.results_filename) as file:
            json_data = json.load(file)
        try :
            for device in json_data['devices']:
                dev = Device(data=device)
                self.devices.append(dev)
        except:
            raise NotImplementedError

    def processClosenessCentrality(self):
        computed_cc = self.physical_network.computeClosenessCentrality()

        for k,v in computed_cc.items():
            device = self.getDeviceByID(k)
            device.closeness_centrality = v

        return computed_cc
