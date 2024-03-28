"""Device module, defines the Device Class

Usage:

    from modules.resources.Device import Device
    dev = Device()
"""

import logging
import random
import json

from typing import List, Dict, Any, Union, Tuple, Optional

from modules.CustomExceptions import NoRouteToHost
from modules.ResourceManagement import fit_resource

class Device:
    """Represents a computing device with limited resources and network capabilities.

    A Device is characterized by resource limitations in terms of CPU, GPU, memory, and disk space.
    Each resource has an associated maximum limit and current usage level. The device also maintains
    a routing table to discover optimal paths to other devices in the network.

    Attributes
    ----------
    device_id : int
        The unique identifier for this device.
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
    proc : List
        A list containing processus that are running on this device.
    closeness_centrality : float
        The closeness centrality metric for this device in the network graph.
    """

    # Devices have a given id
    next_id = 0
    DEFAULT_POSITION = {'x': 0, 'y': 0, 'z': 0}
    DEFAULT_RESOURCE_LIMIT_NVIDIA : Dict[str, Union[int, float]] = {'cpu': 8, 'gpu': 8, 'mem': 8 * 1024, 'disk': 1000 * 1024}
    DEFAULT_RESOURCE_LIMIT_ARM : Dict[str, Union[int, float]] = {'cpu': 16, 'gpu': 0, 'mem': 32 * 1024, 'disk': 1000 * 1024}

    @classmethod
    def _generate_id(cls) -> int:
        """Generates an ID for a new Device instance.

        Returns:
            int: The Device ID.
        """

        result = cls.next_id
        cls.next_id +=1
        return result


    def __init__(self, data: Dict) -> None:
        """Initialize the Device with basic values.

        Args:
            data (Dict): A dictionary containing initialization data.

        """
        default_resource_limit = self.DEFAULT_RESOURCE_LIMIT_NVIDIA.copy() if bool(random.getrandbits(1)) else self.DEFAULT_RESOURCE_LIMIT_ARM.copy()

        if data:
            # Validate and initialize from data dict here
            self.id = data.get('id', Device._generate_id())
            self.position = data.get('position', self.DEFAULT_POSITION.copy())
            self.resource_limit = data.get('resource_limit', default_resource_limit)
            self.current_resource_usage = data.get('current_resource_usage', {key: 0 for key in self.resource_limit})
            self.theoretical_resource_usage = data.get('theoretical_resource_usage', {key: 0 for key in self.resource_limit})
            self.resource_usage_history = data.get('resource_usage_history', {key: [(0, 0)] for key in self.resource_limit})
            self.routing_table = data.get('routing_table', {self.id: (self.id, 0.0)})

        else:
            self.id = Device._generate_id()
            self.position = self.DEFAULT_POSITION.copy()
            self.resource_limit = default_resource_limit
            self.current_resource_usage: Dict[str, Union[int, float]] = {key: 0 for key in self.resource_limit}
            self.theoretical_resource_usage: Dict[str, Union[int, float]] = {key: 0 for key in self.resource_limit}
            self.resource_usage_history = {key: [(0, 0)] for key in self.resource_limit}

            # Routing table, dict {destination:(next_hop, distance)}
            ## Initialized to {self.id:(self.id,0)} as route to self is considered as distance 0
            self.routing_table: Dict[int, Tuple[int, float]] = {self.id: (self.id, 0.0)}

        # TODO : Define a setter and a getter
        self.proc: List = []

        # Value externally set
        self.closeness_centrality = 0.0

        self.color = random.choice(['red','green','blue','yellow','purple','orange','cyan'])


    def __json__(self) -> Dict[str, Any]:
        """
        Returns a dictionary that represents the Device object, suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the Device object's essential fields.
        """
        return {
            "id": self.id,
            "position": self.position,
            "closeness_centrality": self.closeness_centrality,
            "resource_limit": self.resource_limit,
            "resource_usage_history": self.resource_usage_history,
            "routing_table": self.routing_table
        }

    @property
    def id(self) -> int:
        """
        Retrieves the device's ID.

        Returns:
            int: The device ID.
        """
        return self._id

    @id.setter
    def id(self, id: int) -> None:
        """
        Sets the device's ID and reinitializes its routing table.

        This method sets the device's ID and resets the routing table to
        only include the device itself with a distance of 0.

        Args:
            id (int): The new device ID to be set.
        """

        # Set the new ID
        self._id = id

        # Reset the routing table
        self.routing_table = {self.id: (self.id, 0)}

        # Log the change
        logging.debug(f"Device ID changed to {id}, routing_table reset.")


    @property
    def position(self) -> Dict[str, float]:
        return self._position

    @position.setter
    def position(self, position: Dict[str, Any]) -> None:
        """"
        Sets the device's position in a 3D space.

        Args:
            position (Dict[str, Any]): A dictionary containing the x, y, and z coordinates for the device's position.
        """

        self._position = position
        logging.debug(f"Device {self.id}'s position has been updated to {self.position}")


    @property
    def resource_limit(self) -> Dict[str, Union[int, float]] :
        return self._resource_limit

    @resource_limit.setter
    def resource_limit(self, resources: Dict[str,Union[int, float]]) -> None:
        """
        Sets all device resource limits. This overwrites any previous limits.

        Any previous resource limits are set to zero before updating to new values. This ensures that
        only the new set of resources are available.

        Args:
            resources (Dict[str,Union[int, float]]): A dictionary containing all the resource limits.

        """

        if not hasattr(self, '_resource_limit'):
            self._resource_limit = {}

        # Zero out previous values for safety.
        for resource in self.resource_limit:
            self.set_device_resource_limit(resource, 0)

        # Set new resource limits using the set_device_resource_limit method.
        for resource, resource_limit in resources.items():
            self.set_device_resource_limit(resource, resource_limit)


    def set_device_resource_limit(self, resource: str, resource_limit: Union[int, float]) -> None:
        """
        Sets the device's resource limit for a given resource type.

        Args:
            resource (str): The type of resource to set.
                Can take any value but try to be consistent between Device and Application.
            resource_limit (Union[int, float]): The maximum limit for the specified resource type.
        """

        if not hasattr(self, '_resource_limit'):
            self._resource_limit = {}

        self._resource_limit[resource] = resource_limit if resource_limit > 0 else 0
        logging.debug(f"Resource limit for {resource} has been set to {self.resource_limit[resource]} on device.")# {self.id}")


    def allocate_device_resource(self, t: int, resource_name: str, resource: float, *, force = False, overconsume = False) -> float:
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


    def allocate_all_resources(self, t: int, resources: Dict[str, float], *, force: bool = False, overconsume: bool = False) -> Dict[str, float]:
        """
        Allocate all resources based on calls to allocate_device_resource.

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
                resource_retrofitting_coefficient = self.allocate_device_resource(t, resource, resource_limit, force = force, overconsume = overconsume)
                retrofitting_dictionary[resource] = resource_retrofitting_coefficient
            except Exception as e:
                # Log the exception and continue with the next resource
                logging.warning(f"Failed to allocate resource {resource}: {e}")

        return retrofitting_dictionary


    def release_device_resource(self, t: int, resource_name: str, resource: float, *, force: bool = False, overconsume: bool = False) -> float:
        """
        Release resource allocation from the device by allocating a negative resource value.

        Args:
            t (int): Current time value.
            resource_name (str): The name of the resource to release.
            resource (float): The quantity of the resource to release.
            force (bool, optional): Forces allocation at the previous moment in time, which might cause discrepancies. Defaults to False.
            overconsume (bool, optional): Allows allocation over the resource limit. Defaults to False.

        Returns:
            float: Retrofitting coefficient returned by allocate_device_resource
        """
        return self.allocate_device_resource(t, resource_name, -resource, force = force, overconsume = overconsume)


    def release_all_resources(self, t: int, resources: Dict[str, float], *, force: bool = False, overconsume: bool = False) -> Dict[str, float]:
        """
        Release all resources based on calls to release_device_resource.

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
                resource_retrofitting_coefficient = self.release_device_resource(t, resource, resource_limit, force = force, overconsume = overconsume)
                retrofitting_dictionary[resource] = resource_retrofitting_coefficient
            except Exception as e:
                # Log the exception and continue with the next resource
                logging.warning(f"Failed to release resource {resource}: {e}")

        return retrofitting_dictionary


    def get_device_resource_usage(self, resource: str) -> Union[int, float]:
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


    def report_on_value(self, time: int, *, force: bool = False, resources: Optional[List[str]] = None) -> List:
        """Append the last resource usage value to the history at a specific time.

        Args:
            time (int): The current time value.
            force (bool, optional): Force the operation even if max_time is greater than time. Defaults to False.
            resources (Optional[List[str]], optional): List of resource types to report on. Defaults to ['cpu', 'gpu', 'mem', 'disk'].

        Returns:
            List[Tuple[int, Union[int, float]]]: A list of reported data.
        """

        resources = resources or ['cpu', 'gpu', 'mem', 'disk']
        max_time = max(self.resource_usage_history[resource][-1][0] for resource in resources)
        reported_data: List[Tuple[int, Union[int, float]]] = []

        if max_time > time and not force:
            return reported_data
            # raise AttributeError("Unable to report on values at the specified time")

        for resource in resources:
            last_value = self.resource_usage_history[resource][-1][1]
            self.resource_usage_history[resource].append((time, last_value))
            reported_data.append((time, last_value))

        return reported_data


    def add_to_routing_table(self, destination_id: int, next_hop_id: int, distance_destination: float) -> None:
        """
        Adds a new destination or update an existing one in the routing table
        Reminder - routing table element are : {destination:(next_hop, distance)}

        Generates a rounting table progressively by adding devices
        Path are not considered, only next hop and distance
        Single path for now

        Args:
            destination_id (int)
                Device ID of the destination point
            next_hop_id (int)
                Device ID of the next hop in the path to destination
            distance_destination (int)
                distance from device (self) to destination (destination_id), when passing through device (next_hop_id), distance is arbitrary, can be actual distance, number of hops, ...

        """
        existing_value = self.routing_table.get(destination_id, (None, float('inf')))
        _, existing_distance = existing_value

        if distance_destination < existing_distance:
            self.routing_table[destination_id] = (next_hop_id, distance_destination)


    def get_route_info(self, destination_id: int) -> Tuple[int, float]:
        """Returns the next hop and distance for a given destination.

        Args:
            destination_id (int): The ID of the destination device.

        Returns:
            Tuple[int, float]: The next hop ID and the distance to the destination.

        Raises:
            NoRouteToHost: If there is no route to the destination.
        """

        # We check if the destination is known
        try:
            # If it is known, we return the associated values
            return self.routing_table[destination_id]
        except KeyError:
            raise NoRouteToHost(f'No route to host {destination_id}')


    @property
    def resource_usage_history(self) -> Dict[str, List[Tuple[int, Union[int, float]]]]:
        """Get the resource usage history.

        Returns:
            Dict[str, List[Tuple[int, Union[int, float]]]]: The resource usage history.
        """
        return self._resource_usage_history

    @resource_usage_history.setter
    def resource_usage_history(self, resource_history: Dict[str, List[Tuple[int, Union[int, float]]]]) -> None:
        """Set all the resource usage history.

        Should not be used except for visualisation tasks

        Args:
            resource_history (Dict[str, List[Tuple[int, Union[int, float]]]]): The new resource usage history.
        """
        self._resource_usage_history = resource_history


    @property
    def closeness_centrality(self) -> float:
        """Gets the closeness centrality of the device.

        Returns:
            float: The closeness centrality value.
        """
        return self._closeness_centrality

    @closeness_centrality.setter
    def closeness_centrality(self, cc: float) -> None:
        """Sets the closeness centrality of the device.

        Args:
            cc (float): The new closeness centrality value.
        """
        self._closeness_centrality = float(cc)