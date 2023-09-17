"""
Device module, defines the Device Class

Usage:

    from modules.resources.Device import Device
    dev = Device()
"""

import logging

import json

from typing import List, Dict, Union

from modules.CustomExceptions import NoRouteToHost

from modules.ResourceManagement import fit_resource

class Device:
    """
    A device
    A Device is defined as a group of values : CPU, GPU, Memory, Disk space
    Each value is set twice, the maximal value as #_limit and current_use as #_usage
    Additionally, each device has a form of routing table, the routing table stores the next_hop value and distance from the device to each other device in the network

    Attributes:
    -----------
    id : `int`
        Device ID
    position : `dict`
        Device position (in meters, from (0,0,0) origin)
        defaults : {'x':0, 'y':0, 'z':0}
    resource_limit : `dict`
        Device maximal resource values
        defaults : {'cpu' : 2, 'gpu' : 2, 'mem' : 4 * 1024, 'disk' : 250 * 1024}
    current_resource_usage : `dict`
        Current usage for each device feature
        defaults : {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}
    theoretical_resource_usage : `dict`
        Theoretical usage for each device feature
        defaults : {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}
    resource_usage_history : `dict`
        Resource usage changes history
        Init : {'cpu' : [(0,0)], 'gpu' : [(0,0)], 'mem' : [(0,0)], 'disk' : [(0,0)]}
    routing_table : `dict`
        Single path routing table, dictionary of destination:(next_hop, distance)
        Init : {self.id:(self.id,0)}
    proc : <List>`Processus`
        List of `Processus` running on the device
    """

    # Devices have a given id
    next_id = 0


    @classmethod
    def _generate_id(cls):
        """
        Class method for id generation
        Assigns id then increment for next generation

        Args:
        -----
            None

        Returns:
        --------
        result : `int`
            Device ID
        """

        result = cls.next_id
        cls.next_id +=1
        return result


    def __init__(self, data: dict) -> None:
        """
        Initializes the device with basic values
        Assigns ID, initial position, resource values, routing table and resource limits
        """

        # ID setting
        self.id = Device._generate_id()

        # Device Position in the area considered, initialized to {'x':0, 'y':0, 'z':0}
        self.position = dict()

        # Maximal limit for each device feature
        self.resource_limit = dict()

        # Current usage for each device feature
        self.current_resource_usage = dict()

        # Theoretical usage for each device feature
        self.theoretical_resource_usage = dict()

        # Resource usage history
        self.resource_usage_history = dict()

        # Routing table, dict {destination:(next_hop, distance)}
        ## Initialized to {self.id:(self.id,0)} as route to self is considered as distance 0
        self.routing_table = dict()

        try:
            self.initFromDict(data)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize from dict: {e}") from e


        self.proc = list()


    def __json__(self) -> str:
        """
        Returns a JSON string that represents the Device object.

        Returns:
        --------
        str
            A JSON string representing the Device object.
        """

        data_dict = {
            "id" : self.id,
            "position" : self.position,
            "resource_limit" : self.resource_limit,
            "resource_usage_history" : self.resource_usage_history,
            "routing_table" : self.routing_table
        }

        return json.dumps(data_dict, indent=4)


    def setDeviceID(self, id: int) -> None:
        """
        Used to set a device's ID by hand if necessary
        This will reinitialize the device's routing table to {self.id:(self.id,0)}

        Args:
        -----
        id : `int`
            New device ID

        Returns:
        --------
            None
        """

        self.id = id

        self.routing_table = {self.id:(self.id,0)}


    def getDeviceID(self):
        """
        Returns device ID

        Returns:
        --------
        id : `int`
            device ID
        """

        return self.id


    def setDevicePosition(self, position: dict):
        """
        Sets device position in a 3D space

        Args:
        -----
        position : `dict`
            Positions dictionary
        """

        self.position = position


    def setDeviceResourceLimit(self, resource: str, resource_limit: float):
        """
        Sets Device Resource (CPU, GPU, Mem, Disk) Limit

        Args:
        -----
        resource : `str`
            resource name
        resource_limit : `float`
            quantity of a given resource to set as device maximal limit
        """

        self.resource_limit[resource] = resource_limit


    def setAllResourceLimit(self, resources: dict):
        """
        Sets All Device Resource (CPU, GPU, Mem, Disk) Limit

        Sets Previous values to zero for safety

        Args:
        -----
        resources : `dict`
            dictionary of all device resources
        """

        # Set all previous values to Zero
        for resource in self.resource_limit:
            self.setDeviceResourceLimit(resource, 0)

        for resource, resource_limit in resources.items():
            self.setDeviceResourceLimit(resource, resource_limit)


    def allocateDeviceResource(self, t: int, resource_name: str, resource: float, force = False, overconsume = False) -> float:
        """
        allocate a given amount of Device Resource

        Args:
        -----
        t : `int`
            current time value
        resource_name : `str`
            Name for the allocated resource
        resource : `float`
            value for the quantity of Resource requested
        force : `bool`
            Forces allocation at previous moment in time (might cause discrepencies), defaults to False
        overconsume : `bool`
            Allow for allocation over Resource limit, defaults to False

        Returns:
        --------
            retrofitting_coefficient : value to propagate to remaining processus execution to slow/fasten processus time
        """

        previous_time, previous_value = self.resource_usage_history[resource_name][-1]

        if previous_time <= t or force:

            try:
                retrofiting_coefficient = self.current_resource_usage[resource_name] / self.theoretical_resource_usage[resource_name]
            except ZeroDivisionError:
                retrofiting_coefficient = 1


            self.theoretical_resource_usage[resource_name] += resource

            if self.theoretical_resource_usage[resource_name] < 0:
                self.theoretical_resource_usage[resource_name] = 0

            if overconsume:
                self.current_resource_usage[resource_name] = self.theoretical_resource_usage[resource_name]
            else:
                if self.theoretical_resource_usage[resource_name] <= self.resource_limit[resource_name]:
                    self.current_resource_usage[resource_name] = self.theoretical_resource_usage[resource_name]
                else:
                    retrofiting_coefficient = fit_resource(self.theoretical_resource_usage[resource_name], self.resource_limit[resource_name])
                    self.current_resource_usage[resource_name] = self.resource_limit[resource_name]

            if previous_value != self.current_resource_usage[resource_name]:
                if previous_time != t:
                    self.resource_usage_history[resource_name].append((t-1, previous_value))
                    self.resource_usage_history[resource_name].append((t, self.current_resource_usage[resource_name]))
                else:
                    self.resource_usage_history[resource_name][-1] = (t, self.current_resource_usage[resource_name])

            return retrofiting_coefficient

        else:
            raise ValueError("Current time is before previous time")


    def allocateAllResources(self, t, resources, force = False, overconsume = False):
        """
        Allocate all resources based on calls to allocateDeviceResource

        Warning: Does not propagate the retrofitting coefficient for now

        Args:
        -----
        t : `int`
            current time value
        resources : `dict`
            dictionary of all device resources
        force : `bool`
            Forces allocation at previous moment in time (might cause discrepencies), defaults to False
        overconsume : `bool`
            Allow for allocation over Resource limit, defaults to False

        """

        for resource, resource_limit in resources.items():
            self.allocateDeviceResource(t, resource, resource_limit, force, overconsume)


    def releaseDeviceResource(self, t, resource_name, resource, force = False, overconsume = False):
        """
        Release resource allocation from Device, by allocating negative resource value with a call to allocateDeviceResource

        Warning: Does not propagate the retrofitting coefficient for now

        Args:
        -----
        t : `int`
            current time value
        resource_name : `str`
            Name for the allocated resource
        resource : `float`
            value for the quantity of Resource requested
        force : `bool`
            Forces allocation at previous moment in time (might cause discrepencies), defaults to False
        overconsume : `bool`
            Allow for allocation over Resource limit, defaults to False
        """

        self.allocateDeviceResource(t, resource_name, -resource, force, overconsume)


    def releaseAllResources(self, t, resources, force = False, overconsume = False):
        """
        Release all resources based on calls to releaseDeviceResource

        Warning: Does not propagate the retrofitting coefficient for now

        Args:
        -----
        t : `int`
            current time value
        resources : `dict`
            dictionary of all device resources
        force : `bool`
            Forces allocation at previous moment in time (might cause discrepencies), defaults to False
        overconsume : `bool`
            Allow for allocation over Resource limit, defaults to False
        """

        for resource, resource_limit in resources.items():
            self.releaseDeviceResource(t, resource, resource_limit, force, overconsume)


    def getDeviceResourceUsage(self, resource):
        if self.current_resource_usage[resource] == self.resource_usage_history[resource][-1][1]:
            return self.current_resource_usage[resource]
        else:
            raise ValueError("Please use the associated allocation function to allocate resources to prevent this message")


    def reportOnValue(self, time, force=False):

        resources = ['cpu', 'gpu', 'mem', 'disk']

        max_time = max(self.resource_usage_history[resource][-1][0] for resource in resources)

        if max_time <= time or force:
            for resource in resources:
                self.resource_usage_history[resource].append((time,self.resource_usage_history[resource][-1][1]))

    # Generates a rounting table progressively by adding devices
    # Path are not considered, only next hop and distance
    # Single path for now
    def addToRoutingTable(self, destination_id, next_hop_id, distance_destination):#, distance_next_hop):
        """
        Adds a new destination or update an existing one in the routing table
        Reminder - routing table element are : {destination:(next_hop, distance)}

        Args:
        -----
        destination_id : `int`
            Device ID of the destination point
        next_hop_id : `int`
            Device ID of the next hop in the path to destination
        distance_destination : `int`
            distance from device (self) to destination (destination_id), when passing through device (next_hop_id), distance is arbitrary, can be actual distance, number of hops, ...

        Returns:
        --------
            None
        """
        # First we check if the destination is already in the table
        if destination_id in self.routing_table:
            # We check if we need to change the existing value
            if distance_destination < self.routing_table[destination_id][1]:
                # Update the existing value if the new one is lower (the lower the better)
                self.routing_table[destination_id] = (next_hop_id,distance_destination)
        else:
            # Add the new value if no previous value
            self.routing_table[destination_id] = (next_hop_id,distance_destination)


    # Returns the values associated to the route from the device to the destination
    def getRouteInfo(self, destination_id):
        """
        Returns the values associated to the route from the device to the destination

        Args:
        -----
        destination_id : `int`
            Device ID of the destination point

        Returns:
        --------
        (next_hop, distance) : (`int`, `float`)
            next hop in the routing table to reach destination, distance from host to destination

        Raises:
        -------
        NoRouteToHost : `KeyError`
            If destination is not in routing table
        """
        # We check if the destination is known
        try:
            #if destination_id in self.routing_table:
            # If it is known, we return the associated values
            return self.routing_table[destination_id]
        except KeyError:
            raise NoRouteToHost(
                f'No route to host {destination_id}'
            )
            # If not, we return placeholder values (device_id = -1 and distance = 1000)
            # We might change this to raise and error such as "no route to host"
            #return (-1, 1000)

    def initFromDict(self, data):

        try:
            self.setDeviceID(data['id'])
        except KeyError as ke:
            logging.error(f"Error loading device resource data, setting values to default : {ke}")

        try:
            self.setDevicePosition(data['position'])
        except KeyError as ke:
            logging.error(f"Error loading device resource data, setting values to default : {ke}")
            self.position = {'x': 0, 'y': 0, 'z': 0}

        try:
            self.setAllResourceLimit(data['resource_limit'])
        except KeyError as ke:
            logging.error(f"Error loading device resource data, setting values to default : {ke}")
            self.setAllResourceLimit({'cpu': 2, 'gpu': 2, 'mem': 4 * 1024, 'disk': 250 * 1024})

        for key in self.resource_limit:
            self.current_resource_usage[key] = 0
            self.theoretical_resource_usage[key] = 0
            self.resource_usage_history[key] = [(0,0)]

        try:
            self.routing_table = data['routing_table']
        except KeyError as ke:
            logging.error(f"Error loading device routing table, setting values to default : {ke}")
            self.routing_table = {self.id:(self.id,0)}