import logging
from modules.Path import Path
from modules.Environment import Environment

MAX_TENTATIVES = 2000

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

    def __init__(self, event_name, queue, app, device_id, event_time=None):
        """
            app : Application, application to place
            device : Device, first device to try placement, \"Placement Request Receptor\" device
        """
        super().__init__(event_name, queue, event_time)
        self.application_to_place = app
        self.deployment_starting_point = device_id

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

        if proc.cpu_request + device.getDeviceResourceUsage('cpu') <= device.resource_limit['cpu']:
            if proc.gpu_request + device.getDeviceResourceUsage('gpu') <= device.resource_limit['gpu']:
                if proc.mem_request + device.getDeviceResourceUsage('mem')  <= device.resource_limit['mem']:
                    if proc.disk_request + device.getDeviceResourceUsage('disk')  <= device.resource_limit['disk']:
                        return True
        return False

    def reservable_bandwidth(self, env, path, bandwidth_needed):
        """
        Checks if a given bandwidth can be reserved along a given path.

        Args:
            env : Environment
            path : Path
            bandwidth_needed : Bandwidth to allocate on the Path

        Returns:
            Boolean, True if bandwidth can be reserved, else False
        """
        return bandwidth_needed <= path.minBandwidthAvailableonPath(env)


    def linkability(self, env, deployed_app_list, proc_links):
        """
        Checks if a newly deployed processus can be linked to already deployed processus in a given app by checking the link quality on all Paths between the newly deployed processus and already deployed ones.

        Args:
            env : Environment
            deployed_app_list : list of devices on which deployment is proposed
            proc_links : Application.proc_links, len(Application.num_procs)*len(Application.num_procs) matrix indicating necessary bandwidth on each virtual link between application processus members

        Returns:
            Boolean, True if all the interconnexions are possible with given bandwidths, False if at least one is impossible.
        """
        new_device_id = deployed_app_list[-1]
        for i in range(len(deployed_app_list)):
            new_path = Path()
            new_path.path_generation(env, new_device_id, deployed_app_list[i])
            if not self.reservable_bandwidth(env, new_path, proc_links[i][len(deployed_app_list)-1]):
                return False
        return True


    def process(self, env):
        """
        Tries to place a multi-processus application from a given device

        # Application will be deployed on device if possible, else the deployment will be tried on closest devices until all devices are explored

        Args:
            env : Environment
        """

        deployment_latency_test = 0

        deployment_success = True
        # Get ordered device distance

        deployed_onto_devices = list()
        first_dev_exclusion_list = list()

        logging.debug(f"Placement procedure from {self.deployment_starting_point}")

        device = env.getDeviceByID(self.deployment_starting_point)

        deployment_success = True

        tentatives = 0

        while len(deployed_onto_devices) < self.application_to_place.num_procs and tentatives < len(env.getDevices())*len(env.getDevices()):

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
                        proc_list.append(self.application_to_place.processus_list[i])

                proc_list.append(self.application_to_place.processus_list[len(deployed_onto_devices)])

                new_proc = sum(proc_list)

                if self.deployable_proc(new_proc, env.getDeviceByID(device_id)):

                    logging.debug(f"Placement possible on device {device_id}")

                    deployed_onto_devices.append(device_id)

                    deployment_latency_test += deployment_latency

                    if self.linkability(env, deployed_onto_devices, self.application_to_place.proc_links):

                        # deploy links
                        for i in range(len(deployed_onto_devices)):
                            new_path = Path()
                            new_path.path_generation(env, device_id, deployed_onto_devices[i])
                            for path_id in new_path.physical_links_path:
                                if env.physical_network_links[path_id] is not None:
                                    pass
                                    #physical_network_links[path_id].useBandwidth(app.proc_links[len(deployed_onto_devices)-1][i])
                                    #operational_latency += physical_network_links[path_id].getPhysicalNetworkLinkLatency()
                                else:
                                    logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {env.physical_network_links[path_id]}")

                        break
                    else:
                        deployed_onto_devices.pop()
                else:
                    logging.debug(f"Impossible to deploy on {device_id}, testing next closest device")

        if (not deployment_success) or (tentatives == MAX_TENTATIVES) or len(deployed_onto_devices)!=self.application_to_place.num_procs :
            deployed_onto_devices = list()

        if len(deployed_onto_devices) !=0:
            logging.debug(f"application id : {self.application_to_place.id} , {self.application_to_place.num_procs} processus deployed on {deployed_onto_devices}")
        else:
            logging.debug(f"application id : {self.application_to_place.id} , {self.application_to_place.num_procs} processus not deployed")

        if deployed_onto_devices:
            Deploy("Deployment", self.queue, self.application_to_place, deployed_onto_devices, event_time=int((self.get_time()+deployment_latency_test)/10)*10).add_to_queue()
        else:
            prev_time, prev_value = env.count_rejected_application[-1]

            if env.current_time == prev_time:
                env.count_rejected_application[-1][1] += 1
            else:
                env.count_rejected_application.append((env.current_time, prev_value+1))


        return deployment_latency_test, deployed_onto_devices

class Deploy(Event):

    def __init__(self, event_name, queue, app, deployed_onto_devices, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.application_to_deploy = app
        self.devices_destinations = deployed_onto_devices

    def process(self, env):

        operational_latency = 0

        logging.info(f"Deploying application id : {self.application_to_deploy.id} , {self.application_to_deploy.num_procs} processus on {self.devices_destinations}")

        for i in range(self.application_to_deploy.num_procs):

            device_id = self.devices_destinations[i]

            logging.info(f"Deploying processus : {self.application_to_deploy.processus_list[i].id} device {device_id}")

            allocation_request = {'cpu': self.application_to_deploy.processus_list[i].cpu_request,
                                'gpu': self.application_to_deploy.processus_list[i].gpu_request,
                                'mem': self.application_to_deploy.processus_list[i].mem_request,
                                'disk': self.application_to_deploy.processus_list[i].disk_request}

            env.getDeviceByID(device_id).allocateAllResources(self.time, allocation_request)

            # deploy links
            for j in range(i):
                new_path = Path()
                new_path.path_generation(env, device_id, self.devices_destinations[j])
                for path_id in new_path.physical_links_path:
                    if env.physical_network_links[path_id] is not None:
                        env.physical_network_links[path_id].useBandwidth(self.application_to_deploy.proc_links[i-1][j])
                        operational_latency += env.physical_network_links[path_id].getPhysicalNetworkLinkLatency()
                    else:
                        logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {env.physical_network_links[path_id]}")

        self.application_to_deploy.setDeploymentInfo(self.devices_destinations)

        Undeploy("Release", self.queue, self.application_to_deploy, event_time=int(self.get_time()+self.application_to_deploy.duration)).add_to_queue()

        return True

class Deploy_Proc(Event):

    def __init__(self, event_name, queue, app, proc, device_destination_id, event_time=None, last=False, synchronization_time = 10):
        super().__init__(event_name, queue, event_time)
        self.proc_to_deploy = proc
        self.device_destination_id = device_destination_id
        self.last_proc = last
        self.app = app
        self.synchronization_time = synchronization_time

    def process(self, env):

        logging.info(f"Deploying processus : {self.proc.id} on {self.device_destination_id}")

        allocation_request = {'cpu': self.proc_to_deploy.cpu_request,
                            'gpu': self.proc_to_deploy.gpu_request,
                            'mem': self.proc_to_deploy.mem_request,
                            'disk': self.proc_to_deploy.disk_request}

        env.getDeviceByID(self.device_destination_id).allocateAllResources(self.time, allocation_request)

        if self.last_proc:
            Sync("Synchronize", self.queue, self.app, event_time=int(self.get_time()+self.synchronization_time)).add_to_queue()


        return True

class Fit(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        raise NotImplementedError('Process not implemented')


class Sync(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        pass
        #raise NotImplementedError('Process not implemented')

    # Will need to do that at some point
    # self.application_to_deploy.setDeploymentInfo(self.devices_destinations)



class Undeploy(Event):

    def __init__(self, event_name, queue, app, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.application_to_undeploy = app


    def process(self, env):

        logging.debug(f"Undeploying application id : {self.application_to_undeploy.id} , {self.application_to_undeploy.deployment_info}")

        for process,device_id in self.application_to_undeploy.deployment_info.items():

            logging.debug(f"Undeploying processus : {process.id} device {device_id}")

            release_request = {'cpu': process.cpu_request, 'gpu': process.gpu_request, 'mem': process.mem_request, 'disk': process.disk_request}

            env.getDeviceByID(device_id).releaseAllResources(self.time, release_request)

            # undeploy links
            """
            for j in range(i):
                new_path = Path()
                new_path.path_generation(env, device_id, self.devices_destinations[j])
                for path_id in new_path.physical_links_path:
                    if env.physical_network_links[path_id] is not None:
                        env.physical_network_links[path_id].useBandwidth(self.application_to_deploy.proc_links[i-1][j])
                        operational_latency += env.physical_network_links[path_id].getPhysicalNetworkLinkLatency()
                    else:
                        logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {env.physical_network_links[path_id]}")
            """

        return True


class RegularCheck(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        raise NotImplementedError('Process not implemented')


class FinalReport(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)

    def process(self, env):
        for device in env.devices:
            device.reportOnValue(self.get_time())

