import logging
from modules.resource.Path import Path
from modules.Environment import Environment
from modules.fullstateprocessing.FullStateProcessing import CeilingUnlimitedMigration
import json

MAX_TENTATIVES = 5

class Event():
    """An event with event_number occurs at a specific time ``event_time`` and involves a specific
        event type ``event_type``. Comparing two events amounts to figuring out which event occurs first """

    def __init__(self, event_name, queue, event_time=None):

        self.name = event_name
        self.queue = queue
        self.time = event_time
        self.priority = 0

        if event_time is None:
            self.time = queue.env.current_time
        elif event_time < queue.env.current_time:
            self.time = queue.env.current_time


    def __lt__(self, other):
        """ Returns True if self.event_time < other.event_time"""
        return (self.time < other.time) or (self.time == other.time and self.priority < other.priority)


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


    def set_time(self, event_time=None):
        self.time = event_time
        if event_time is None:
            self.time = self.queue.env.current_time
        elif event_time < self.queue.env.current_time:
            self.time = self.queue.env.current_time


class Placement(Event):

    def __init__(self, event_name, queue, app, device_id, event_time=None):
        """
            app : Application, application to place
            device : Device, first device to try placement, \"Placement Request Receptor\" device
        """
        super().__init__(event_name, queue, event_time)
        self.application_to_place = app
        self.deployment_starting_point = device_id
        self.tentatives = 1
        self.priority = 2


    def __json__(self):
        return {
            "placement_time" : self.get_time(),
            "requesting_device" : self.deployment_starting_point,
            "application" : self.application_to_place
        }


    def retry(self, event_time):
        if self.tentatives < MAX_TENTATIVES:
            self.tentatives +=1
            self.set_time(event_time=event_time)
            self.add_to_queue()
            logging.info(f"Placement set back to future time, from {self.get_time()} to {int((self.get_time()+15*60*1000)/10)*10}")
        else:
            logging.info(f"{MAX_TENTATIVES} failures on placing app, dropping the placement")


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

        for resource in proc.resource_request:
            if proc.resource_request[resource] + device.getDeviceResourceUsage(resource) > device.resource_limit[resource]:
                return False
        return True


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

        deployment_success = True
        # Get ordered device distance

        deployed_onto_devices = list()
        deployment_times = list()
        deployment_success = True

        logging.debug(f"Placement procedure from {self.deployment_starting_point}")

        if env.config.dry_run:
            self.application_to_place.setDeploymentInfo(deployed_onto_devices)
            env.currenty_deployed_apps.append(self.application_to_place)
            Undeploy("Release", self.queue, self.application_to_place, event_time=int(self.get_time()+self.application_to_place.duration)).add_to_queue()
            return deployment_times, deployed_onto_devices

        try:
            device = env.getDeviceByID(self.deployment_starting_point)
        except:
            device = env.getRandomDevice()
            logging.debug(f"Placement procedure from other device {device.getDeviceID()}")

        distance_from_device = {i: device.routing_table[i][1] for i in device.routing_table}
        sorted_distance_from_device = sorted(distance_from_device.items(), key=lambda x: x[1])

        pref_proc = dict()
        for proc in self.application_to_place.processus_list:
            pref_proc[proc.id] = list()
            for dev_id,dev_latency in sorted_distance_from_device:
                device = env.getDeviceByID(dev_id)
                if self.deployable_proc(proc, device):
                    pref_proc[proc.id].append((dev_id, dev_latency))

        matching = dict()
        matching_latency = dict()
        to_match  = self.application_to_place.getAppProcsIDs()

        while len(to_match)!=0:
            proc_id = to_match.pop(0)

            try:
                deployed, deployment_latency  = pref_proc[proc_id].pop(0)
            except IndexError:
                deployment_success = False
                break

            if deployed not in matching.values():
                matching[proc_id] = deployed
                matching_latency[proc_id] = deployment_latency
            else:
                matching_procs = [self.application_to_place.getAppProcByID(proc) for proc,dev in matching.items() if dev == deployed]
                agglomerated = sum(matching_procs)# + proc
                if self.deployable_proc(agglomerated, env.getDeviceByID(dev_id)):
                    matching[proc_id] = deployed
                    matching_latency[proc_id] = deployment_latency
                else:
                    min_proc_deployed = min([self.application_to_place.getAppProcByID(proc) for proc,dev in matching.items() if dev == deployed])
                    if self.application_to_place.getAppProcByID(proc_id) > min_proc_deployed:
                        min_proc_deployed_id = min_proc_deployed.getProcessusID()
                        to_match.append(min_proc_deployed_id)
                        matching[proc_id] = deployed
                        matching_latency[proc_id] = deployment_latency
                        matching.pop(min_proc_deployed_id, None)
                        matching_latency.pop(min_proc_deployed_id, None)
                    else:
                        to_match.append(proc_id)

        if deployment_success:

            prev_time, prev_value = env.count_accepted_application[-1]
            _, prev_tentative = env.count_tentatives[-1]

            for proc_id in self.application_to_place.getAppProcsIDs():
                deployed_onto_devices.append(matching[proc_id])
                deployment_times.append(matching_latency[proc_id])

            logging.info(f"Placement Module : application id : {self.application_to_place.id} , {self.application_to_place.num_procs} processus deployed on {deployed_onto_devices}")

            for i in range(len(deployed_onto_devices)):
                Deploy_Proc("Deployment Proc", self.queue, self.application_to_place, deployed_onto_devices, i, event_time=int((self.get_time()+deployment_times[i])/10)*10, last=(i+1==len(deployed_onto_devices))).add_to_queue()

            if env.current_time == prev_time:
                env.count_accepted_application[-1][1] += 1
                env.count_tentatives[-1][1] += self.tentatives
            else:
                env.count_accepted_application.append([env.current_time, prev_value+1])
                env.count_tentatives.append([env.current_time, prev_tentative+self.tentatives])

        else:
            prev_time, prev_value = env.count_rejected_application[-1]

            logging.info(f"Placement Module : application id : {self.application_to_place.id} , {self.application_to_place.num_procs} processus not deployed")

            if env.current_time == prev_time:
                env.count_rejected_application[-1][1] += 1
            else:
                env.count_rejected_application.append([env.current_time, prev_value+1])

            # We could ask for a retry after 15 mins

            logging.info(f"Placement set back to future time, from {self.get_time()} to {int((self.get_time()+15*60*1000)/10)*10}")
            self.retry(event_time=int((self.get_time()+15*60*1000)/10)*10)

        return deployment_times, deployed_onto_devices


class Deploy_Proc(Event):

    def __init__(self, event_name, queue, app, deployed_onto_devices, index, event_time=None, last=False, synchronization_time = 10):
        super().__init__(event_name, queue, event_time)
        self.app = app
        self.devices_destinations = deployed_onto_devices
        self.proc_to_deploy = self.app.processus_list[index]
        self.device_destination_id = self.devices_destinations[index]
        self.last_proc = last
        self.app = app
        self.synchronization_time = synchronization_time
        self.priority = 3

    def process(self, env):

        logging.debug(f"Deploying processus : {self.proc_to_deploy.id} on {self.device_destination_id}")

        allocation_request = {'cpu': self.proc_to_deploy.resource_request['cpu'],
                            'gpu': self.proc_to_deploy.resource_request['gpu'],
                            'mem': self.proc_to_deploy.resource_request['mem'],
                            'disk': self.proc_to_deploy.resource_request['disk']}

        env.getDeviceByID(self.device_destination_id).allocateAllResources(self.time, allocation_request)

        if self.last_proc:
            Sync("Synchronize", self.queue, self.app, self.devices_destinations, event_time=int(self.get_time()+self.synchronization_time)).add_to_queue()


        return True

class Fit(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        raise NotImplementedError('Process not implemented')


class Sync(Event):
    def __init__(self, event_name, queue, app, deployed_onto_devices, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.app = app
        self.devices_destinations = deployed_onto_devices
        self.priority = 4

    def process(self, env):
        operational_latency = 0

        # Allocate links
        for i in range(self.app.num_procs):
            device_id = self.devices_destinations[i]
            for j in range(i):
                new_path = Path()
                new_path.path_generation(env, device_id, self.devices_destinations[j])
                for path_id in new_path.physical_links_path:
                    if env.physical_network_links[path_id] is not None:
                        env.physical_network_links[path_id].useBandwidth(self.app.proc_links[i-1][j])
                        operational_latency += env.physical_network_links[path_id].getPhysicalNetworkLinkLatency()
                    else:
                        logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {env.physical_network_links[path_id]}")

        # Set Deployment info
        self.app.setDeploymentInfo(self.devices_destinations)
        env.currenty_deployed_apps.append(self.app)

        # Run
        Undeploy("Release", self.queue, self.app, event_time=int(self.get_time()+self.app.duration)).add_to_queue()


class Undeploy(Event):

    def __init__(self, event_name, queue, app, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.application_to_undeploy = app
        self.priority = 1


    def process(self, env):

        logging.debug(f"Undeploying application id : {self.application_to_undeploy.id} , {self.application_to_undeploy.deployment_info}")

        for process,device_id in self.application_to_undeploy.deployment_info.items():

            logging.debug(f"Undeploying processus : {process.id} device {device_id}")

            release_request = {'cpu': process.resource_request['cpu'], 'gpu': process.resource_request['gpu'], 'mem': process.resource_request['mem'], 'disk': process.resource_request['disk']}

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
        env.currenty_deployed_apps.remove(self.application_to_undeploy)
        return True


class RegularCheck(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        raise NotImplementedError('Process not implemented')


class Organize(Event):
    def __init__(self, event_name, queue, application_to_place, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.priority = 5
        self.application_to_place = application_to_place

    def process(self, env: Environment):

        dev_matrix = env.extractDevicesResources()
        proc_matrix = env.extractCurrentlyDeployedAppData()
        instance = CeilingUnlimitedMigration(proc_matrix, dev_matrix)

        x = instance.processing()

        return x


class FinalReport(Event):
    def __init__(self, event_name, queue, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.priority = 0

    def process(self, env):
        for device in env.devices:
            device.reportOnValue(self.get_time())

