import logging

from modules.events.Event import Event

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

            env.get_device_by_id(int(device_id)).release_all_resources(self.time, release_request) # Error here, TODO: Better handling of ids types

            # undeploy links
            """
            for j in range(i):
                new_path = Path()
                new_path.path_generation(env, device_id, self.devices_destinations[j])
                for path_id in new_path.physical_links_path:
                    if env.physical_network_links[path_id] is not None:
                        env.physical_network_links[path_id].use_bandwidth(self.application_to_deploy.proc_links[i-1][j])
                        operational_delay += env.physical_network_links[path_id].get_physical_network_link_delay()
                    else:
                        logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {env.physical_network_links[path_id]}")
            """
        env.currently_deployed_apps.remove(self.application_to_undeploy)
        return True

