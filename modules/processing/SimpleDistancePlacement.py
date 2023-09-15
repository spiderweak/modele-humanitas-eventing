class PlacementCalculation:
    raise NotImplementedError

class SimplaDistancePlacement(PlacementCalculation):

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

        device = env.getDeviceByID(self.deployment_starting_point)
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

