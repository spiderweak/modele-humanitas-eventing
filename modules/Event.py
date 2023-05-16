import logging
from modules.Path import Path
from modules.Environment import Environment

MAX_TENTATIVES = 2

class Event():
    """An event with event_number occurs at a specific time ``event_time`` and involves a specific
        event type ``event_type``. Comparing two events amounts to figuring out which event occurs first """

    def __init__(self, event_name, queue, event_time=None):

        self.name = event_name
        self.queue = queue
        self.time = event_time

        if event_time is None:
            self.time = queue.env.current_time
        elif event_time < queue.env.current_time:
            self.time = queue.env.current_time


    def __lt__(self, other):
        """ Returns True if self.event_time < other.event_time"""
        return self.time < other.time


    def add_to_queue(self):
        self.queue.put(self)

    def get_event(self):
        """Gets the first event in the event list"""
        event = self.queue.get()
        return event

    def get_name(self):
        """ returns event name"""
        return self.name

    def get_time(self):
        """ returns event time"""
        return self.time


class Placement(Event):

    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)

    # Let's define how to deploy an application on the system.
    def deployable_proc(self, proc, device):
        """
        Checks if a given process can be deployed onto a device.

        Args:
            proc : Processus
            device : Device

        Returns:
            Boolean, True if deployable, else False
        """

        

        if proc.cpu_request + device.getDeviceCPUUsage() <= device.cpu_limit:
            logging.debug(proc.gpu_request)
            logging.debug(device.getDeviceGPUUsage())
            logging.debug(device.gpu_limit)
            if proc.gpu_request + device.getDeviceGPUUsage() <= device.gpu_limit:
                if proc.mem_request + device.getDeviceMemUsage() <= device.mem_limit:
                    if proc.disk_request + device.getDeviceDiskUsage() <= device.disk_limit:
                        return True
        return False

    def reservable_bandwidth(self, path, bandwidth_needed, physical_network_link_list):
        """
        Checks if a given bandwidth can be reserved along a given path.

        Args:
            path : Path
            bandwidth_needed : Bandwidth to allocate on the Path
            physical_network_link_list : List(PhysicalNetworkLink), List of physical links to evaluate the minimal bandwidth available on the Path 

        Returns:
            Boolean, True if bandwidth can be reserved, else False
        """
        return bandwidth_needed <= path.minBandwidthAvailableonPath(physical_network_link_list)


    def linkability(self, env, deployed_app_list, proc_links):
        """
        Checks if a newly deployed processus can be linked to already deployed processus in a given app by checking the link quality on all Paths between the newly deployed processus and already deployed ones.

        Args:
            deployed_app_list : int, Device ID of the Device on which the last processus deployed
            proc_links : Application.proc_links, len(Application.num_procs)*len(Application.num_procs) matrix indicating necessary bandwidth on each virtual link between application processus members
            device_list : List of devices, used to get devices IDs and routing table, non modified (Global variable now, but globals are bad)
            physical_network_link_list : List(PhysicalNetworkLink), List of physical links to evaluate the minimal bandwidth available on the Path 

        Returns:
            Boolean, True if all the interconnexions are possible with given bandwidths, False if at least one is impossible.
        """
        new_device_id = deployed_app_list[-1]
        for i in range(len(deployed_app_list)):
            new_path = Path()
            new_path.path_generation(env.devices, new_device_id, deployed_app_list[i])
            if not self.reservable_bandwidth(new_path, proc_links[i][len(deployed_app_list)-1], env.physical_network_links):
                return False
        return True


    def process(self, env, app, device_id):
        """
        Tries to place a multi-processus application from a given device

        # Application will be deployed on device if possible, else the deployment will be tried on closest devices until all devices are explored

        Args:
            env : Environment
            app : Application, application to place
            device : Device, first device to try placement, \"Placement Request Receptor\" device

        Returns:
            (deployment_success, latency, operational_latency, deployed_onto_devices)
                deployment_success : Bool, deployment success boolean
                latency : float, cumulative latency along deployment procedure
                operational_latency : float, cumulative latency between deployed processus based on links quality
                deployed_onto_devices : list, device ids for all devices onto application were deployed
        """

        deployment_success = True
        # Get ordered device distance

        deployed_onto_devices = list()
        first_dev_exclusion_list = list()

        logging.debug(f"Placement procedure from {device_id}")

        device = env.getDeviceByID(device_id)

        deployment_success = True

        tentatives = 0

        while len(deployed_onto_devices) < app.num_procs and tentatives < MAX_TENTATIVES:

            tentatives +=1

            if len(deployed_onto_devices) == 0 and len(first_dev_exclusion_list)==0:
                distance_from_device = {i: device.routing_table[i][1] for i in device.routing_table}
                sorted_distance_from_device = sorted(distance_from_device.items(), key=lambda x: x[1])
                logging.debug(f"Source {sorted_distance_from_device[0][0]}")
            else:
                if len(deployed_onto_devices)!= 0:
                    new_source_device = env.getDeviceByID(deployed_onto_devices[-1])
                else:
                    distance_from_device = {i: device.routing_table[i][1] for i in device.routing_table}
                    if len(first_dev_exclusion_list) == len(distance_from_device):
                        deployment_success = False
                        break
                    else:
                        for j in first_dev_exclusion_list:
                            if j in distance_from_device:
                                del distance_from_device[j]
                        sorted_distance_from_device = sorted(distance_from_device.items(), key=lambda x: x[1])
                        new_source_device = sorted_distance_from_device[0][0]

                distance_from_device = {i: new_source_device.routing_table[i][1] for i in new_source_device.routing_table}
                sorted_distance_from_device = sorted(distance_from_device.items(), key=lambda x: x[1])

                logging.debug(f"Switching source to {sorted_distance_from_device[0][0]}")

            for device_id, deployment_latency in sorted_distance_from_device:

                logging.debug(f"Testing placement on device {device_id}")

                proc_list = list()

                for i in range(len(deployed_onto_devices)):
                    if device_id == deployed_onto_devices[i]:
                        proc_list.append(app.processus_list[i])

                proc_list.append(app.processus_list[len(deployed_onto_devices)])

                new_proc = sum(proc_list)

                if self.deployable_proc(new_proc, env.getDeviceByID(device_id)):

                    logging.debug(f"Placement possible on device {device_id}")

                    deployed_onto_devices.append(device_id)

                    if self.linkability(env, deployed_onto_devices, app.proc_links):

                        # deploy links
                        for i in range(len(deployed_onto_devices)):
                            new_path = Path()
                            new_path.path_generation(env.devices, device_id, deployed_onto_devices[i])
                            for path_id in new_path.physical_links_path:
                                if env.physical_network_links[path_id] is not None:
                                    pass
                                    #physical_network_link_list[path_id].useBandwidth(app.proc_links[len(deployed_onto_devices)-1][i])
                                    #operational_latency += physical_network_link_list[path_id].getPhysicalNetworkLinkLatency()
                                else:
                                    logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {env.physical_network_links[path_id]}")

                        break
                    else:
                        deployed_onto_devices.pop()
                else:
                    logging.debug(f"Impossible to deploy on {device_id}, testing next closest device")

        if (not deployment_success) or (tentatives == MAX_TENTATIVES):
            for i in range(len(deployed_onto_devices)):
                device_id = deployed_onto_devices[i]

                device_deployed_onto = env.getDeviceByID(device_id)

                env.getDeviceByID(device_id).setDeviceCPUUsage(device_deployed_onto.cpu_usage - app.processus_list[i].cpu_request)
                env.getDeviceByID(device_id).setDeviceGPUUsage(device_deployed_onto.gpu_usage - app.processus_list[i].gpu_request)
                env.getDeviceByID(device_id).setDeviceDiskUsage(device_deployed_onto.disk_usage - app.processus_list[i].disk_request)
                env.getDeviceByID(device_id).setDeviceMemUsage(device_deployed_onto.mem_usage - app.processus_list[i].mem_request)

            deployed_onto_devices = list()

        if len(deployed_onto_devices) !=0:
            print(f"application id : {app.id} , {app.num_procs} processus deployed on {deployed_onto_devices}")
        else:
            print(f"application id : {app.id} , {app.num_procs} processus not deployed")

        return deployed_onto_devices


class Deploy(Event):

    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)

    def process(self, env, app, deployed_onto_devices):
        operational_latency = 0

        logging.debug(f"Placing application id : {app.id} , {app.num_procs} processus on {deployed_onto_devices}")

        for i in range(app.num_procs):

            device_id = deployed_onto_devices[i]

            logging.debug(f"Deploying processus : {app.processus_list[i].id} device {device_id}")

            device_deployed_onto = devices_list[device_id]

            device_deployed_onto.setDeviceCPUUsage(self.time, device_deployed_onto.getDeviceCPUUsage() + app.processus_list[i].cpu_request)
            device_deployed_onto.setDeviceGPUUsage(self.time, device_deployed_onto.getDeviceGPUUsage() + app.processus_list[i].gpu_request)
            device_deployed_onto.setDeviceDiskUsage(self.time, device_deployed_onto.getDeviceMemUsage() + app.processus_list[i].disk_request)
            device_deployed_onto.setDeviceMemUsage(self.time, device_deployed_onto.getDeviceDiskUsage() + app.processus_list[i].mem_request)

            devices_list[device_id] = device_deployed_onto


            # deploy links
            for j in range(i):
                new_path = Path()
                new_path.path_generation(devices_list, device_id, deployed_onto_devices[j])
                for path_id in new_path.physical_links_path:
                    if physical_network_link_list[path_id] is not None:
                        physical_network_link_list[path_id].useBandwidth(app.proc_links[i-1][j])
                        operational_latency += physical_network_link_list[path_id].getPhysicalNetworkLinkLatency()
                    else:
                        logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {physical_network_link_list[path_id]}")

        app.setDeploymentInfo(deployed_onto_devices)

        return True


class Fit(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        raise NotImplementedError('Process not implemented')


class Undeploy(Event):

    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        raise NotImplementedError('Process not implemented')

    def process(self, app):
        pass


class RegularCheck(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        raise NotImplementedError('Process not implemented')


