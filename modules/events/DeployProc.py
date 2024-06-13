import logging

from modules.EventQueue import EventQueue

from modules.events.Event import Event
from modules.events.Sync import Sync

from modules.resource.Application import Application

from typing import Optional, Dict, Any, List

class DeployProc(Event):

    DEFAULT_SYNCRONIZATION_TIME = 10

    def __init__(self, event_name: str, queue: EventQueue, app: Application, deployed_onto_devices: List, link_allocation: Dict, index: int, event_time: Optional[int] =None, last: bool=False, synchronization_time = DEFAULT_SYNCRONIZATION_TIME):
        """
        Initializes a DeployProc object to manage the placement of an application.

        Args:
            event_name (str): Name of the event.
            queue (EventQueue): The event queue to which this event belongs.
            app (Application): The application to place.
            event_time (Optional[int]): Time at which the event occurs. Defaults to None.
        """

        super().__init__(event_name, queue, event_time)

        self.app = app
        self.devices_destinations = deployed_onto_devices
        self.link_allocation = link_allocation
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

        env.get_device_by_id(int(self.device_destination_id)).allocate_all_resources(self.time, allocation_request) # Error here, TODO: Better handling of ids types

        self.update_global_data(env)

        if self.last_proc:
            Sync("Synchronize", self.queue, self.app, self.devices_destinations, self.link_allocation, event_time=int(self.time+self.synchronization_time)).add_to_queue()

        return True


    def update_global_data(self, env) -> None:
        """Update global data based on the environment state and allocation request."""

        env.data.integrity_check(self.time)

        allocation_request = {'cpu': self.proc_to_deploy.resource_request['cpu'],
                              'gpu': self.proc_to_deploy.resource_request['gpu'],
                              'mem': self.proc_to_deploy.resource_request['mem'],
                              'disk': self.proc_to_deploy.resource_request['disk']}

        # Update the current row with the new allocation request
        env.data.update_data(self.time, 'cpu_current', allocation_request['cpu'])
        env.data.update_data(self.time, 'gpu_current', allocation_request['gpu'])
        env.data.update_data(self.time, 'memory_current', allocation_request['mem'])
        env.data.update_data(self.time, 'disk_current', allocation_request['disk'])

        # Increase the number of currently hosted procs by 1
        env.data.update_data(self.time, 'currently_hosted_procs', 1)
