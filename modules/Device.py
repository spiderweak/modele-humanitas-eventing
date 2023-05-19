"""
Device module, defines the Device Class

Usage:

"""

from modules.CustomExceptions import NoRouteToHost

from modules.ResourceManagement import fit_resource

class Device:
    # A Device is defined as a group of values : CPU, GPU, Memory, Disk space
    # Each value is set twice, the maximal value as #_limit and current_use as #_usage
    # Additionally, each device has a form of routing table, the routing table stores the next_hop value and distance from the device to each other device in the network

    # Devices have a given id

    id = 0


    @classmethod
    def _generate_id(cls):
        """
        Class method for id generation
        Assigns id then increment for next generation

        Args:
            None

        Returns:
            result : int, Device ID
        """
        result = cls.id
        cls.id +=1
        return result


    def __init__(self) -> None:
        """
        Initializes the device with basic values
        Assigns ID, initial position, resource values, routing table and resource limits
        """
        # ID setting
        self.id = Device._generate_id()

        # Device Position in the area considered

        self.position = {'x':0, 'y':0, 'z':0}

        # Maximal limit for each device feature
        self.resource_limit = {'cpu' : 2, 'gpu' : 2, 'mem' : 4 * 1024, 'disk' : 250 * 1024}

        # Current usage for each device feature
        self.current_resource_usage = {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}

        # Theorical usage for each device feature
        self.theorical_resource_usage = {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}

        # Resource usage history
        self.resource_usage_history = {'cpu' : [(0,0)], 'gpu' : [(0,0)], 'mem' : [(0,0)], 'disk' : [(0,0)]}
        ## CPU Usage (float) history, changes value when current usage changes, initialized at (0,0)
        self.cpu_usage_history = self.resource_usage_history['cpu']
        ## GPU Usage (float) in number of GPUs, initialized to 0
        self.gpu_usage_history = self.resource_usage_history['gpu']
        ## RAM Usage (float) in MegaBytes, initialized to 0
        self.mem_usage_history = self.resource_usage_history['mem']
        ## Disk Usage (float) in MegaBytes, initialized to 0
        self.disk_usage_history = self.resource_usage_history['disk']

        # Routing table, dict {destination:(next_hop, distance)}
        ## Initialized to {self.id:(self.id,0)} as route to self is considered as distance 0
        self.routing_table = {self.id:(self.id,0)}


    def setDeviceID(self, id):
        """
        Used to set a device's ID by hand if necessary
        This will reinitialize the device's routing table to {self.id:(self.id,0)}

        Args:
            id : int, new device ID

        Returns:
            None
        """
        self.id = id
        self.routing_table = {self.id:(self.id,0)}


    def getDeviceID(self):
        """
        Returns device ID

        Args:
            None

        Returns:
            id : int, device ID
        """
        return self.id


    def setDevicePosition(self, position):
        """
        Sets device position in a 3D space

        Args:
        ----
        position : `dict`
            Positions dictionary
        """

        self.position = position


    def setDeviceResourceLimit(self, resource, resource_limit):
        """
        Sets Device Resource (CPU, GPU, Mem, Disk) Limit

        Args:
        ----
        resource : `str`
            resource name
        resource_limit : `float`
            quantity of a given resource to set as device maximal limit

        """
        self.resource_limit[resource] = resource_limit

    def setAllResourceLimit(self, resources):
        # Set all previous values to Zero
        for resource in self.resource_limit:
            self.setDeviceResourceLimit(resource, 0)

        for resource, resource_limit in resources.items():
            self.setDeviceResourceLimit(resource, resource_limit)

    def allocateDeviceCPU(self, t, cpu, force = False, overconsume = False):
        """
        allocate a given amount of Device CPU

        Args:
            t : int, time value
            cpu : float, value for the quantity of CPU requested
            force : bool, Forces allocation at previous moment in time (might cause discrepencies), defaults to False
            overconsume : bool, Allow for allocation over GPU limit, defaults to False

        Returns:
            retrofitting_coefficient : value to propagate to remaining processus execution to slow/fasten processus time
        """

        previous_time, previous_value = self.cpu_usage_history[-1]

        if previous_time <= t or force:

            try:
                retrofiting_coefficient = self.current_resource_usage['cpu'] / self.theorical_resource_usage['cpu']
            except ZeroDivisionError:
                retrofiting_coefficient = 1


            self.theorical_resource_usage['cpu'] += cpu

            if self.theorical_resource_usage['cpu'] < 0:
                self.theorical_resource_usage['cpu'] = 0

            if overconsume:
                self.current_resource_usage['cpu'] = self.theorical_resource_usage['cpu']
            else:
                if self.theorical_resource_usage['cpu'] <= self.resource_limit['cpu']:
                    self.current_resource_usage['cpu'] = self.theorical_resource_usage['cpu']
                else:
                    retrofiting_coefficient = fit_resource(self.theorical_resource_usage['cpu'], self.resource_limit['cpu'])
                    self.current_resource_usage['cpu'] = self.resource_limit['cpu']

            if previous_value != self.current_resource_usage['cpu']:
                if previous_time != t:
                    self.cpu_usage_history.append((t-1, previous_value))
                    self.cpu_usage_history.append((t, self.current_resource_usage['cpu']))
                else:
                    self.cpu_usage_history[-1] = (t, self.current_resource_usage['cpu'])

            return retrofiting_coefficient

        else:
            raise ValueError("Current time is before previous time")


    def releaseDeviceCPU(self, t, cpu, force = False, overconsume = False):
        self.allocateDeviceCPU(t, -cpu, force, overconsume)


    def getDeviceCPUUsage(self):
        if self.current_resource_usage['cpu'] == self.cpu_usage_history[-1][1]:
            return self.current_resource_usage['cpu']
        else:
            raise ValueError("Please use the associated allocation function to allocate resources to prevent this message")


    def allocateDeviceGPU(self, t, gpu, force = False, overconsume = False):
        """
        allocate a given amount of Device GPU

        Args:
            t : int, time value
            gpu : float, value for the quantity of GPU requested
            force : bool, Forces allocation at previous moment in time (might cause discrepencies), defaults to False
            overconsume : bool, Allow for allocation over GPU limit, defaults to False

        Returns:
            retrofitting_coefficient : value to propagate to remaining processus execution to slow/fasten processus time
        """

        previous_time, previous_value = self.gpu_usage_history[-1]

        if previous_time <= t or force:

            try:
                retrofiting_coefficient = self.current_resource_usage['gpu'] / self.theorical_resource_usage['gpu']
            except ZeroDivisionError:
                retrofiting_coefficient = 1

            self.theorical_resource_usage['gpu'] += gpu

            if self.theorical_resource_usage['gpu'] < 0:
                self.theorical_resource_usage['gpu'] = 0

            if overconsume:
                self.current_resource_usage['gpu'] = self.theorical_resource_usage['gpu']
            else:
                if self.theorical_resource_usage['gpu'] <= self.resource_limit['gpu']:
                    self.current_resource_usage['gpu'] = self.theorical_resource_usage['gpu']
                else:
                    retrofiting_coefficient = fit_resource(self.theorical_resource_usage['gpu'], self.resource_limit['gpu'])
                    self.current_resource_usage['gpu'] = self.resource_limit['gpu']

            if previous_value != self.current_resource_usage['gpu']:
                if previous_time != t:
                    self.gpu_usage_history.append((t-1, previous_value))
                    self.gpu_usage_history.append((t, self.current_resource_usage['gpu']))
                else:
                    self.gpu_usage_history[-1] = (t, self.current_resource_usage['gpu'])

            return retrofiting_coefficient

        else:
            raise ValueError("Current time is before previous time")


    def releaseDeviceGPU(self, t, gpu, force = False, overconsume = False):
        self.allocateDeviceGPU(t, -gpu, force, overconsume)


    def getDeviceGPUUsage(self):
        if self.current_resource_usage['gpu'] == self.gpu_usage_history[-1][1]:
            return self.current_resource_usage['gpu']
        else:
            raise ValueError("Please use the associated allocation function to allocate resources to prevent this message")


    def allocateDeviceMem(self, t, mem, force = False, overconsume = False):
        """
        allocate a given amount of Device Memory

        Args:
            t : int, time value
            mem : float, value for the quantity of Memory requested
            force : bool, Forces allocation at previous moment in time (might cause discrepencies), defaults to False
            overconsume : bool, Allow for allocation over GPU limit, defaults to False

        Returns:
            retrofitting_coefficient : value to propagate to remaining processus execution to slow/fasten processus time
        """

        previous_time, previous_value = self.mem_usage_history[-1]

        if previous_time <= t or force:

            try:
                retrofiting_coefficient = self.current_resource_usage['mem'] / self.theorical_resource_usage['mem']
            except ZeroDivisionError:
                retrofiting_coefficient = 1

            self.theorical_resource_usage['mem'] += mem

            if self.theorical_resource_usage['mem'] < 0:
                self.theorical_resource_usage['mem'] = 0

            if overconsume:
                self.current_resource_usage['mem'] = self.theorical_resource_usage['mem']
            else:
                if self.theorical_resource_usage['mem'] <= self.resource_limit['mem']:
                    self.current_resource_usage['mem'] = self.theorical_resource_usage['mem']
                else:
                    retrofiting_coefficient = fit_resource(self.theorical_resource_usage['mem'], self.resource_limit['mem'])
                    self.current_resource_usage['mem'] = self.resource_limit['mem']

            if previous_value != self.current_resource_usage['mem']:
                if previous_time != t:
                    self.mem_usage_history.append((t-1, previous_value))
                    self.mem_usage_history.append((t, self.current_resource_usage['mem']))
                else:
                    self.mem_usage_history[-1] = (t, self.current_resource_usage['mem'])

            return retrofiting_coefficient

        else:
            raise ValueError("Current time is before previous time")

    def releaseDeviceMem(self, t, mem, force = False, overconsume = False):
        self.allocateDeviceMem(t, -mem, force, overconsume)

    def getDeviceMemUsage(self):
        if self.current_resource_usage['mem'] == self.mem_usage_history[-1][1]:
            return self.current_resource_usage['mem']
        else:
            raise ValueError("Please use the associated allocation function to allocate resources to prevent this message")


    def allocateDeviceDisk(self, t, disk, force = False, overconsume = False):
        """
        allocate a given amount of Device Disk Space

        Args:
            t : int, time value
            disk : float, value for the quantity of Disk Usage requested
            force : bool, Forces allocation at previous moment in time (might cause discrepencies), defaults to False
            overconsume : bool, Allow for allocation over GPU limit, defaults to False

        Returns:
            retrofitting_coefficient : value to propagate to remaining processus execution to slow/fasten processus time
        """

        previous_time, previous_value = self.disk_usage_history[-1]

        if previous_time <= t or force:

            try:
                retrofiting_coefficient = self.current_resource_usage['disk'] / self.theorical_resource_usage['disk']
            except ZeroDivisionError:
                retrofiting_coefficient = 1

            self.theorical_resource_usage['disk'] += disk

            if self.theorical_resource_usage['disk'] < 0:
                self.theorical_resource_usage['disk'] = 0

            if overconsume:
                self.current_resource_usage['disk'] = self.theorical_resource_usage['disk']
            else:
                if self.theorical_resource_usage['disk'] <= self.resource_limit['disk']:
                    self.current_resource_usage['disk'] = self.theorical_resource_usage['disk']
                else:
                    retrofiting_coefficient = fit_resource(self.theorical_resource_usage['disk'], self.resource_limit['disk'])
                    self.current_resource_usage['disk'] = self.resource_limit['disk']

            if previous_value != self.current_resource_usage['disk']:
                if previous_time != t:
                    self.disk_usage_history.append((t-1, previous_value))
                    self.disk_usage_history.append((t, self.current_resource_usage['disk']))
                else:
                    self.disk_usage_history[-1] = (t, self.current_resource_usage['disk'])

            return retrofiting_coefficient

        else:
            raise ValueError("Current time is before previous time")


    def releaseDeviceDisk(self, t, disk, force = False, overconsume = False):
        self.allocateDeviceDisk(t, -disk, force, overconsume)


    def getDeviceDiskUsage(self):
        if self.current_resource_usage['disk'] == self.disk_usage_history[-1][1]:
            return self.current_resource_usage['disk']
        else:
            raise ValueError("Please use the associated allocation function to allocate resources to prevent this message")


    def reportOnValue(self, time, force=False):
        previous_cpu_time, previous_cpu_value = self.cpu_usage_history[-1]
        previous_gpu_time, previous_gpu_value = self.gpu_usage_history[-1]
        previous_mem_time, previous_mem_value = self.mem_usage_history[-1]
        previous_disk_time, previous_disk_value = self.disk_usage_history[-1]

        if max(previous_cpu_time, previous_gpu_time,previous_mem_time, previous_disk_time) <= time or force:
            self.cpu_usage_history.append((time,previous_cpu_value))
            self.gpu_usage_history.append((time,previous_gpu_value))
            self.mem_usage_history.append((time,previous_mem_value))
            self.disk_usage_history.append((time,previous_disk_value))

    # Generates a rounting table progressively by adding devices
    # Path are not considered, only next hop and distance
    # Single path for now
    def addToRoutingTable(self, destination_id, next_hop_id, distance_destination):#, distance_next_hop):
        """
        Adds a new destination or update an existing one in the routing table
        Reminder - routing table element are : {destination:(next_hop, distance)}

        Args:
            destination_id : int, Device ID of the destination point
            next_hop_id : int, Device ID of the next hop in the path to destination
            distance_destination : int, distance from device (self) to destination (destination_id), when passing through device (next_hop_id), distance is arbitrary, can be actual distance, number of hops, ...

        Returns:
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
            destination_id : int, Device ID of the destination point

        Returns:
            (next_hop, distance) : (int, float), next hop in the routing table to reach destination, distance from host to destination

        Raises:
            DestinationUnknown: If destination is not in routing table -- To Be Implemented
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
