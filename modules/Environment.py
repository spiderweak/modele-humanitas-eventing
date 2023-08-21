from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Application import Application
from modules.resource.Device import Device
from modules.resource.PhysicalNetwork import PhysicalNetwork
from modules.CustomExceptions import (NoRouteToHost, DeviceNotFoundError)
from modules.ResourceManagement import custom_distance

import logging
import json
from tqdm import tqdm
import random
import networkx as nx
import os
import matplotlib.pyplot as plt
import numpy as np
class Environment(object):
    """
    The ``Environment`` class mostly serves as a structure for storing information about the environment (configuration, device info, application info, network link...)

    Attributes:
    -----------
    current_time: `int`
        The date and time of the current event.
    config: `Config`
        Environment configuration exported from the ``Config`` class
    devices : list of `Device`
        List of ``Device`` objects storing device information (position, resource availability, routing table...)
    applications: list of `Application` to deploy
        List of ``Application`` objects storing application information (processus, virtual links... )
    physical_network_links: list of physical network links
        List of Physical links between devices, connectivity matrix
    """


    def __init__(self):
        """
        The ``Environment`` class is initialized to empty lists, None or 0 values
        """

        self.current_time = 0

        self.config = None

        self.applications = []
        self.currenty_deployed_apps = []
        self.devices = []
        self.devices_links = []
        self.physical_network = PhysicalNetwork()
        self.count_rejected_application=[[0,0]]
        self.count_accepted_application=[[0,0]]
        self.count_tentatives=[[0,0]]

        self.TIME_PERIOD = 24 * 60 * 60 * 100



    def setConfig(self, config):
        """
        Sets the configuration based on a given instanciated `Config` class.

        Args:
        -----
        config: `Config`
            Environment configuration generated in the `Config` module
        """
        self.config = config


    def getDevices(self):
        return self.devices


    def getDeviceByID(self, dev_id):
        """
        Gets the first `Device` which ID matches `dev_id`.
        `Device` IDs are supposed to be unique by construction.

        Args:
        -----
        dev_id: `int`
            device identifier
        """
        for device in self.devices:
            if device.id == int(dev_id):
                return device
        raise DeviceNotFoundError


    def addDevice(self, device):
        """ Adds a new `Device` to the devices list"""
        self.devices.append(device)


    def getApplicationByID(self, app_id):
        """
        Gets the first `Application` which ID matches `app_id`.
        `Application` IDs are supposed to be unique by construction.
        """
        for application in self.applications:
            if application.id == app_id:
                return application


    def addApplication(self, application):
        """ Adds a new `Application` to the applications list"""
        self.applications.append(application)


    def removeApplication(self, app_id):
        """
        Removes all `Application` with given `app_id`
        `Application` IDs are supposed to be unique, so only one app should be removed
        """
        self.applications = [application for application in self.applications if application.id != app_id]

    def generateApplicationList(self):
        for i in tqdm(range(self.config.number_of_applications)):
            # Generating 1 random application
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
        """

        number_of_devices = len(self.getDevices())

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
        try:
            with open(self.config.devices_file) as file:
                devices_list = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Please add devices list in argument, default value is devices.json in current directory")

        for device in devices_list['devices']:
            self.devices.append(Device(data=device))


    def importApplications(self):
        try:
            with open(self.config.applications_file) as file:
                applications_list = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Please add application list in argument, default value is applications.json in current directory")
        except json.decoder.JSONDecodeError:
            pass

        for application in applications_list:
            self.applications.append(Application(data=application))


    def importLinks(self):
        with open(self.config.devices_template_filename) as file:
            json_data = json.load(file)
        try :

            number_of_devices = len(self.getDevices())

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
                source_device.addToRoutingTable(target_device.id, target_device.id,link['weight'])
                # target_device.addToRoutingTable(source_device.id, source_device.id,link['weight'])

                new_physical_network_link = PhysicalNetworkLink(source_device.id, target_device.id, size=number_of_devices)
                if link['id'] != new_physical_network_link.id:
                    new_physical_network_link.setLinkID(link['id'])
                self.physical_network.addLink(new_physical_network_link)

        except KeyError as ke:
            if ke.args[0] == 'links':
                for device_1 in self.getDevices():
                    device_1_id = device_1.getDeviceID()
                    for device_2 in self.getDevices():
                        device_2_id = device_2.getDeviceID()
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
        with open(self.config.devices_template_filename) as file:
            json_data = json.load(file)

        try:
            for device in json_data['devices']:
                self.devices.append(Device(data=device))
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
                    device['id'] = device_data['id']
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
        ax.set_zlim(0, 50)
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
                extracted_data[resource][device.getDeviceID()] = device.resource_limit[resource]

        if filename:
            json_string = json.dumps(extracted_data, default=lambda o: list(o), indent=4)
            with open(filename, 'w') as file:
                file.write(json_string)

        return extracted_data


    def extractCurrentyDeployedAppData(self):
        # Generate an array with length equal to number of apps currently deployed
        # Generate an array in this array with length equal to number of procs for each apps
        # Generate a dict with each resource (cpu, gpu, memory, disk) request for each proc for each app
        # return and export to csv
        pass

    def extractValues(self):

        self.physical_network.extractNetworkMatrix()
        self.extractDevicesResources()

