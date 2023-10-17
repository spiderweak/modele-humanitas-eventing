
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

