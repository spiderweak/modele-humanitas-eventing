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

        if self.application_to_undeploy.num_procs > 1:
            for i in range(self.application_to_undeploy.num_procs):
                for j in range(i+1, self.application_to_undeploy.num_procs):
                    if self.application_to_undeploy.links_deployment_info[(i,j)]:
                        self.application_to_undeploy.links_deployment_info[(i,j)].free_bandwidth_on_path(env,self.application_to_undeploy.proc_links[i][j])

            # undeploy links
            """
            for j in range(i):
                new_path = Path()
                new_path.path_generation(env, device_id, self.devices_destinations[j])
                for path_id in new_path.physical_links_path:
                    if env.physical_network_links[path_id] is not None:
                        env.physical_network_links[path_id].use_bandwidth(self.application_to_deploy.proc_links[i-1][j])
                        operational_delay += env.physical_network_links[path_id].delay
                    else:
                        logging.error(f"Physical network link error, expexted PhysicalNetworkLink, got {env.physical_network_links[path_id]}")
            """
        env.currently_deployed_apps.remove(self.application_to_undeploy)

        self.update_global_data(env)

        return True

    def update_global_data(self, env) -> None:
        """Update global data based on the environment state and allocation request."""

        env.data.integrity_check(self.time)

        for process,_ in self.application_to_undeploy.deployment_info.items():

            release_request = {'cpu': process.resource_request['cpu'],
                               'gpu': process.resource_request['gpu'],
                               'mem': process.resource_request['mem'],
                               'disk': process.resource_request['disk']}

            # Update the current row with the new allocation request
            env.data.data.at[self.time, 'cpu_current'] -= release_request['cpu']
            env.data.data.at[self.time, 'gpu_current'] -= release_request['gpu']
            env.data.data.at[self.time, 'memory_current'] -= release_request['mem']
            env.data.data.at[self.time, 'disk_current'] -= release_request['disk']

        env.data.data.at[self.time, 'cumulative_app_departure'] += 1

        # Decrease the number of currently hosted procs by num_procs
        env.data.data.at[self.time, 'currently_hosted_procs'] -= self.application_to_undeploy.num_procs

        # Decrease the number of currently hosted applications by 1
        env.data.data.at[self.time, 'currently_hosted_apps'] -= 1


        # TODO : Implement bandwidth deallocation report