"""
Device module, defines the Device Class

Usage:

    from modules.resources.Device import Device
    dev = Device()
"""

import logging
import random
import json

from typing import List, Dict, Any, Union, Tuple

from modules.CustomExceptions import NoRouteToHost

from modules.ResourceManagement import fit_resource

class Device:
    """
    Represents a computing device with limited resources and network capabilities.

    A Device is characterized by resource limitations in terms of CPU, GPU, memory, and disk space.
    Each resource has an associated maximum limit and current usage level. The device also maintains
    a routing table to discover optimal paths to other devices in the network.

    Attributes
    ----------
    device_id : int
        The unique identifier for this device.
    name : str
        A human-readable name for the device.
    location : Tuple[float, float, float]
        The x, y, z coordinates of the device in the network.
    resource_limit : Dict[str, Union[int, float]]
        A dictionary containing the resource limits for the device.
        Keys can be resource names like 'CPU', 'GPU', etc., and the values are the respective limits.
    current_resource_usage : Dict[str, Union[int, float]]
        A dictionary containing the current resource usage for the device.
    theoretical_resource_usage : Dict[str, Union[int, float]]
        A dictionary containing the theoretical resource usage for the device.
    resource_usage_history : Dict[str, List[Tuple[int, Union[int, float]]]]
        A history of resource usage for each type of resource.
        Each history is a list of tuples, where the first element is the time, and the second is the resource usage at that time.
    routing_table : Dict[int, Tuple[int, float]]
        A dictionary representing the routing table for this device.
        Each key is the device_id of a destination, and the value is a tuple (next_hop_id, distance).
    """

    # Devices have a given id
    next_id = 0


    @classmethod
    def _generate_id(cls) -> int:
        """
        Generates an ID for a new Device instance.

        Returns:
            int: The Device ID.
        """

        result = cls.next_id
        cls.next_id +=1
        return result


    def __init__(self, data: Dict) -> None:
        """
        Initialize the Device with basic values.

        Args:
            data (Dict): A dictionary containing initialization data.

        Raises:
            RuntimeError: If initialization from dict fails.
        """

        # ID setting
        self.id = Device._generate_id()

        # Device Position in the area considered, initialized to {'x':0, 'y':0, 'z':0}
        self.position: Dict[str, float] = {}

        # Maximal limit for each device feature
        self.resource_limit: Dict[str, Union[int, float]] = {}

        # Current usage for each device feature
        self.current_resource_usage: Dict[str, Union[int, float]] = {}

        # Theoretical usage for each device feature
        self.theoretical_resource_usage: Dict[str, Union[int, float]] = {}

        # Resource usage history
        self.resource_usage_history: Dict[str, List[Tuple[int, Union[int, float]]]] = {}

        # Routing table, dict {destination:(next_hop, distance)}
        ## Initialized to {self.id:(self.id,0)} as route to self is considered as distance 0
        self.routing_table: Dict[int, Tuple[int, float]] = {self.id: (self.id, 0.0)}

        try:
            self.initFromDict(data)
        except Exception as e:
            logging.error(f"Failed to initialize Device from dict: {e}")
            raise RuntimeError(f"Failed to initialize from dict: {e}") from e

        self.proc: List = []

        self.closeness_centrality: float = 0.0


    def initFromDict(self, data: Dict) -> None:
        """
        Initializes the device instance using the provided dictionary.

        Args:
            data (dict): The dictionary containing device data.

        Returns:
            None
        """

        # Set Device ID
        self.id = data.get('id', Device._generate_id())

        # Set Device Position
        self.position = data.get('position', {'x': 0, 'y': 0, 'z': 0})

        # Set Resource Limits
        default_resource_limit = {
            'cpu': 8, 'gpu': 8, 'mem': 8 * 1024, 'disk': 1000 * 1024
        } if bool(random.getrandbits(1)) else {
            'cpu': 16, 'gpu': 0, 'mem': 32 * 1024, 'disk': 1000 * 1024
        }
        self.resource_limit = data.get('resource_limit', default_resource_limit)

        # Other Resource Attributes based on limit
        self.current_resource_usage = {key: 0 for key in self.resource_limit}
        self.theoretical_resource_usage = {key: 0 for key in self.resource_limit}


        # Set Resource Usage History
        self.resource_usage_history = data.get('resource_usage_history',
                                            {key: [(0, 0)] for key in self.resource_limit})

        # Set Routing Table
        self.routing_table = data.get('routing_table', {self.id: (self.id, 0)})


        try:
            self.setAllResourceLimit(data['resource_limit'])
        except KeyError as ke:
            logging.error(f"Error loading device resource data, setting values to default : {ke}")
            if bool(random.getrandbits(1)):
                # NDC
                self.setAllResourceLimit({'cpu': 16, 'gpu': 0, 'mem': 32 * 1024, 'disk': 1000 * 1024})
            else:
                # Jetson https://connecttech.com/ftp/pdf/nvidia_jetson_orin_datasheet.pdf
                self.setAllResourceLimit({'cpu': 8, 'gpu': 8, 'mem': 8 * 1024, 'disk': 1000 * 1024})


    def __json__(self) -> Dict[str, Any]:
        """
        Returns a dictionary that represents the Device object, suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the Device object's essential fields.
        """
        return {
            "id": self.id,
            "position": self.position,
            "resource_limit": self.resource_limit,
            "resource_usage_history": self.resource_usage_history,
            "routing_table": self.routing_table
        }


    def setDeviceID(self, id: int) -> None:
        """
        Sets the device's ID and reinitializes its routing table.

        This method sets the device's ID and resets the routing table to
        only include the device itself with a distance of 0.

        Args:
            id (int): The new device ID to be set.
        """

        # Set the new ID
        self.id = id

        # Reset the routing table
        self.routing_table = {self.id: (self.id, 0)}

        # Log the change
        logging.debug(f"Device ID changed to {id}, routing_table reset.")


    def getDeviceID(self) -> int:
        """
        Retrieves the device's ID.

        Returns:
            int: The device ID.
        """
        return self.id


    def setDevicePosition(self, position: Dict[str, Any]) -> None:
        """"
        Sets the device's position in a 3D space.

        Args:
            position (Dict[str, Any]): A dictionary containing the x, y, and z coordinates for the device's position.
        """

        self.position = position
        logging.debug(f"Device {self.id}'s position has been updated to {self.position}")


    def setDeviceResourceLimit(self, resource: str, resource_limit: Union[int, float]) -> None:
        """
        Sets the device's resource limit for a given resource type.

        Args:
            resource (str): The type of resource to set.
                Can take any value but try to be consistent between Device and Application.
            resource_limit (Union[int, float]): The maximum limit for the specified resource type.

        Raises:
            ValueError: If the resource type is invalid or the resource limit is non-positive.
        """

        self.resource_limit[resource] = resource_limit if resource_limit > 0 else 0
        logging.debug(f"Resource limit for {resource} has been set to {self.resource_limit[resource]} on device {self.id}")


    def setAllResourceLimit(self, resources: Dict[str,Union[int, float]]) -> None:
        """
        Sets all device resource limits. This overwrites any previous limits.

        Any previous resource limits are set to zero before updating to new values. This ensures that
        only the new set of resources are available.

        Args:
            resources (Dict[str,Union[int, float]]): A dictionary containing all the resource limits.

        """

        # Zero out previous values for safety.
        for resource in self.resource_limit:
            self.setDeviceResourceLimit(resource, 0)

        # Set new resource limits using the setDeviceResourceLimit method.
        for resource, resource_limit in resources.items():
            self.setDeviceResourceLimit(resource, resource_limit)


    def allocateDeviceResource(self, t: int, resource_name: str, resource: float, *, force = False, overconsume = False) -> float:
        """
        Allocates a given amount of device resource.

        Args:
            t (int): Current time value.
            resource_name (str): Name for the allocated resource.
            resource (float): Value for the quantity of resource requested.
            force (bool, optional): Forces allocation at previous moment in time. Defaults to False.
            overconsume (bool, optional): Allows allocation over resource limit. Defaults to False.

        Returns:
            float: Retrofitting coefficient to propagate to remaining processes.

        Raises:
            ValueError: When the current time is before the previous time.
        """

        previous_time, previous_value = self.resource_usage_history[resource_name][-1]

        if previous_time > t and not force:
            raise ValueError("Current time is before previous time")

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

        # Update resource usage history
        if previous_value != self.current_resource_usage[resource_name]:
            if previous_time != t:
                self.resource_usage_history[resource_name].append((t-1, previous_value))
                self.resource_usage_history[resource_name].append((t, self.current_resource_usage[resource_name]))
            else:
                self.resource_usage_history[resource_name][-1] = (t, self.current_resource_usage[resource_name])

        return retrofiting_coefficient


    def allocateAllResources(self, t: int, resources: Dict[str, float], *, force: bool = False, overconsume: bool = False) -> Dict[str, float]:
        """
        Allocate all resources based on calls to allocateDeviceResource.

        Args:
            t (int): current time value.
            resources (dict): dictionary of all device resources.
            force (bool):   Forces allocation at previous moment in time,
                            might cause discrepancies. Defaults to False.
            overconsume (bool): Allow for allocation over Resource limit.
                                Defaults to False.

        Returns:
            Dict[str, float]: Dictionary of retrofitting coefficients for each resource.
        """

        retrofitting_dictionary: Dict[str, float] = {}

        for resource, resource_limit in resources.items():
            try:
                resource_retrofitting_coefficient = self.allocateDeviceResource(t, resource, resource_limit, force = force, overconsume = overconsume)
                retrofitting_dictionary[resource] = resource_retrofitting_coefficient
            except Exception as e:
                # Log the exception and continue with the next resource
                logging.warning(f"Failed to allocate resource {resource}: {e}")

        return retrofitting_dictionary


    def releaseDeviceResource(self, t: int, resource_name: str, resource: float, *, force: bool = False, overconsume: bool = False) -> float:
        """
        Release resource allocation from the device by allocating a negative resource value.

        Args:
            t (int): Current time value.
            resource_name (str): The name of the resource to release.
            resource (float): The quantity of the resource to release.
            force (bool, optional): Forces allocation at the previous moment in time, which might cause discrepancies. Defaults to False.
            overconsume (bool, optional): Allows allocation over the resource limit. Defaults to False.

        Returns:
            float: Retrofitting coefficient returned by allocateDeviceResource
        """
        return self.allocateDeviceResource(t, resource_name, -resource, force = force, overconsume = overconsume)


    def releaseAllResources(self, t: int, resources: Dict[str, float], *, force: bool = False, overconsume: bool = False) -> Dict[str, float]:
        """
        Release all resources based on calls to releaseDeviceResource.

        Note: This method does not propagate the retrofitting coefficient for now.

        Args:
            t (int): Current time value.
            resources (Dict[str, float]): Dictionary of all device resources.
            force (bool, optional): Forces allocation at the previous moment in time, which might cause discrepancies. Defaults to False.
            overconsume (bool, optional): Allows allocation over the resource limit. Defaults to False.

        Returns:
            Dict[str, float]: Dictionary of retrofitting coefficients for each resource.
        """

        retrofitting_dictionary: Dict[str, float] = {}

        for resource, resource_limit in resources.items():
            try:
                resource_retrofitting_coefficient = self.releaseDeviceResource(t, resource, resource_limit, force = force, overconsume = overconsume)
                retrofitting_dictionary[resource] = resource_retrofitting_coefficient
            except Exception as e:
                # Log the exception and continue with the next resource
                logging.warning(f"Failed to release resource {resource}: {e}")

        return retrofitting_dictionary


    def getDeviceResourceUsage(self, resource: str) -> Union[int, float]:
        """
        Retrieve the current usage of a given resource on the device.

        Args:
            resource (str): The name of the resource.

        Returns:
            Union[int, float]: The current resource usage.

        Raises:
            ValueError: If the resource usage is not properly allocated.
        """
        try:
            if self.current_resource_usage[resource] == self.resource_usage_history[resource][-1][1]:
                return self.current_resource_usage[resource]
        except KeyError:
            raise ValueError(f"Resource '{resource}' not found.")

        raise ValueError("Please use the associated allocation function to allocate resources.")


    def reportOnValue(self, time: int, *, force: bool = False) -> None:
        """
        Append the resource usage to the history at a specific time.

        Args:
            time (int): The current time value.
            force (bool, optional): Force the operation even if max_time is greater than time. Defaults to False.

        """
        resources = ['cpu', 'gpu', 'mem', 'disk']
        max_time = max(self.resource_usage_history[resource][-1][0] for resource in resources)

        if max_time <= time or force:
            for resource in resources:
                self.resource_usage_history[resource].append((time, self.resource_usage_history[resource][-1][1]))


    def addToRoutingTable(self, destination_id: int, next_hop_id: int, distance_destination: float) -> None:
        """
        Adds a new destination or update an existing one in the routing table
        Reminder - routing table element are : {destination:(next_hop, distance)}

        Generates a rounting table progressively by adding devices
        Path are not considered, only next hop and distance
        Single path for now

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


    def getRouteInfo(self, destination_id: int) -> Tuple[int, float]:
        """
        Returns the next hop and distance for a given destination.

        Args:
            destination_id (int): The ID of the destination device.

        Returns:
            Tuple[int, float]: The next hop ID and the distance to the destination.

        Raises:
            NoRouteToHost: If there is no route to the destination.
        """

        # We check if the destination is known
        try:
            #if destination_id in self.routing_table:
            # If it is known, we return the associated values
            return self.routing_table[destination_id]
        except KeyError:
            raise NoRouteToHost(f'No route to host {destination_id}')


    def setResourceUsageHistory(self, resource_history: Dict[str, List[Tuple[int, Union[int, float]]]]) -> None:
        """
        Set the resource usage history.

        Args:
            resource_history (Dict[str, List[Tuple[int, Union[int, float]]]]): The new resource usage history.
        """
        self.resource_usage_history = resource_history
