import logging

from modules.events.Event import Event
from modules.events.Sync import Sync

class DeployProc(Event):

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

        env.get_device_by_id(int(self.device_destination_id)).allocate_all_resources(self.time, allocation_request) # Error here, TODO: Better handling of ids types

        if self.last_proc:
            Sync("Synchronize", self.queue, self.app, self.devices_destinations, event_time=int(self.time+self.synchronization_time)).add_to_queue()


        return True
