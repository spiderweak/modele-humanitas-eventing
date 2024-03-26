import logging

from modules.Environment import Environment
from modules.EventQueue import EventQueue

from modules.resource.Application import Application
from modules.resource.Processus import Processus
from modules.resource.Path import Path

from modules.events.Event import Event
from modules.events.Undeploy import Undeploy
from modules.events.DeployProc import DeployProc

from modules.CustomExceptions import DeviceNotFoundError


from typing import Optional, Dict, Any

class Placement(Event):

    MAX_TENTATIVES = 5
    REFERENCE_PRIORITY = 2.0
    FIFTEEN_MINUTES_BACKOFF = 15 * 60 * 1000


    def __init__(self, event_name: str, queue: EventQueue, app: Application, device_id: int, event_time: Optional[int]=None):
        """
        Initializes a Placement object to manage the placement of an application.

        Args:
            event_name (str): Name of the event.
            queue (EventQueue): The event queue to which this event belongs.
            app (Application): The application to place.
            device_id (int): ID of the first device to try for placement, referred to as the "Placement Request Receptor" device.
            event_time (Optional[int]): Time at which the event occurs. Defaults to None.
        """
        super().__init__(event_name, queue, event_time)
        self.application_to_place = app
        self.deployment_starting_point = device_id
        self.tentatives = 1
        self.priority = self._calculate_priority(app)


    def _calculate_priority(self, app: Application) -> float:
        """
        Calculate the priority of the Placement event based on the application's priority.

        Args:
            app (Application): The application to place.

        Returns:
            float: Calculated priority.
        """
        return self.REFERENCE_PRIORITY + float(app.priority / 10)


    def __json__(self) -> Dict[str, Any]:
        """
        Serialize the Placement object into a JSON-serializable dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing key-value pairs of the Placement object's attributes.
                            {
                                "placement_time": time of the placement,
                                "requesting_device": ID of the "Placement Request Receptor" device,
                                "application": Application object to be placed
                            }
        """
        return {
            "placement_time" : self.time,
            "requesting_device" : self.deployment_starting_point,
            "application" : self.application_to_place
        }


    def process(self, env: Environment):
        """
        Tries to place a multi-processus application from a given device
        Args:
            env : Environment
        Returns:
            Tuple[List[int], List[int]]: Deployment times and deployed onto devices (Device ID List)
        """

        logging.debug(f"Placement procedure from {self.deployment_starting_point}")

        if env.config is None:
            raise ValueError("Configuration not set")

        if env.config.dry_run:
            self.application_to_place.set_deployment_info([]) # This will break the dry_run option
            env.currently_deployed_apps.append(self.application_to_place)
            Undeploy("Release", self.queue, self.application_to_place, event_time=int(self.time+self.application_to_place.duration)).add_to_queue()
            return [], []

        try:
            device = env.get_device_by_id(self.deployment_starting_point)
        except DeviceNotFoundError:
            device = env.get_random_device()
            logging.debug(f"Placement procedure from other device {device.id}")




        deployment_success = True
        # Get ordered device distance

        deployed_onto_devices = list()
        deployment_times = list()
        deployment_success = True


        distance_from_device = {i: device.routing_table[i][1] for i in device.routing_table}
        sorted_distance_from_device = sorted(distance_from_device.items(), key=lambda x: x[1])

        pref_proc = dict()
        for proc in self.application_to_place.processus_list:
            pref_proc[proc.id] = list()
            for dev_id, dev_delay in sorted_distance_from_device:
                device = env.get_device_by_id(int(dev_id)) # Error here, TODO: Better handling of ids types
                if self.deployable_proc(proc, device):
                    pref_proc[proc.id].append((dev_id, dev_delay))

        matching = dict()
        matching_delay = dict()
        to_match  = self.application_to_place.get_app_procs_ids()

        while len(to_match)!=0:
            proc_id = to_match.pop(0)

            try:
                deployed, deployment_delay  = pref_proc[proc_id].pop(0)
            except IndexError:
                deployment_success = False
                break

            if deployed not in matching.values():
                matching[proc_id] = deployed
                matching_delay[proc_id] = deployment_delay
            else:
                matching_procs = [self.application_to_place.get_app_proc_by_id(proc) for proc,dev in matching.items() if dev == deployed]
                agglomerated = sum(matching_procs)# + proc # type: ignore
                if self.deployable_proc(agglomerated, env.get_device_by_id(int(dev_id))): # Error here, TODO: Better handling of ids types
                    matching[proc_id] = deployed
                    matching_delay[proc_id] = deployment_delay
                else:
                    min_proc_deployed = min([self.application_to_place.get_app_proc_by_id(proc) for proc,dev in matching.items() if dev == deployed])
                    if self.application_to_place.get_app_proc_by_id(proc_id) > min_proc_deployed:
                        min_proc_deployed_id = min_proc_deployed.id
                        to_match.append(min_proc_deployed_id)
                        matching[proc_id] = deployed
                        matching_delay[proc_id] = deployment_delay
                        matching.pop(min_proc_deployed_id, None)
                        matching_delay.pop(min_proc_deployed_id, None)
                    else:
                        to_match.append(proc_id)

        if deployment_success:

            prev_time, prev_value = env.count_accepted_application[-1]
            _, prev_tentative = env.count_tentatives[-1]

            for proc_id in self.application_to_place.get_app_procs_ids():
                deployed_onto_devices.append(matching[proc_id])
                deployment_times.append(matching_delay[proc_id])

            logging.info(f"Placement Module : application id : {self.application_to_place.id} , {self.application_to_place.num_procs} processus deployed on {deployed_onto_devices}")

            for i in range(len(deployed_onto_devices)):
                DeployProc("Deployment Proc", self.queue, self.application_to_place, deployed_onto_devices, i, event_time=int((self.time+deployment_times[i])/10)*10, last=(i+1==len(deployed_onto_devices))).add_to_queue()

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

            logging.info(f"Placement set back to future time, from {self.time} to {int((self.time+self.FIFTEEN_MINUTES_BACKOFF)/10)*10}")
            self.retry(event_time=int((self.time+self.FIFTEEN_MINUTES_BACKOFF)/10)*10)

        return deployment_times, deployed_onto_devices

    def retry(self, event_time):
        if self.tentatives < self.MAX_TENTATIVES:
            self.tentatives +=1
            self.time = event_time
            self.add_to_queue()
            logging.info(f"Placement set back to future time, from {self.time} to {int((self.time+self.FIFTEEN_MINUTES_BACKOFF)/10)*10}")
        else:
            logging.info(f"{self.MAX_TENTATIVES} failures on placing app, dropping the placement")


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
            if proc.resource_request[resource] + device.get_device_resource_usage(resource) > device.resource_limit[resource]:
                return False
        return True


    def reservable_bandwidth(self, env: Environment, path, bandwidth_needed):
        """
        Checks if a given bandwidth can be reserved along a given path.

        Args:
            env : Environment
            path : Path
            bandwidth_needed : Bandwidth to allocate on the Path

        Returns:
            Boolean, True if bandwidth can be reserved, else False
        """
        return bandwidth_needed <= path.min_bandwidth_available_on_path(env)


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

