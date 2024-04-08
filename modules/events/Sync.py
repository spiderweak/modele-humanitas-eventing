import logging

from modules.events.Event import Event
from modules.events.Undeploy import Undeploy

from modules.resource.Path import Path



class Sync(Event):
    def __init__(self, event_name, queue, app, deployed_onto_devices, link_allocation, event_time=None):
        super().__init__(event_name, queue, event_time)
        self.app = app
        self.devices_destinations = deployed_onto_devices
        self.link_allocation = link_allocation
        self.priority = 4

    def process(self, env):
        operational_delay = 0

        # Allocate links
        for i in range(self.app.num_procs):
            device_id = self.devices_destinations[i]
            for j in range(i):
                new_path = Path()
                new_path.path_generation(env, device_id, self.devices_destinations[j])
                for path_id in new_path.physical_links_path:
                    if env.physical_network_links[path_id] is not None:
                        env.physical_network_links[path_id].use_bandwidth(self.app.proc_links[i-1][j])
                        operational_delay += env.physical_network_links[path_id].delay
                    else:
                        logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {env.physical_network_links[path_id]}")

        # Set Deployment info
        self.app.set_deployment_info(self.devices_destinations)
        self.app.set_links_allocation_info(self.link_allocation)
        env.currently_deployed_apps.append(self.app)

        # Run
        Undeploy("Release", self.queue, self.app, event_time=int(self.time+self.app.duration)).add_to_queue()

