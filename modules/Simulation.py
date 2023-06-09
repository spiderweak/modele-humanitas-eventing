import matplotlib.pyplot as plt
import networkx as nx
import random
import logging

import time

import numpy as np

from tqdm import tqdm

from modules.Application import Application
from modules.EventQueue import EventQueue
from modules.Event import (Event, Placement, Deploy, FinalReport)
from modules.Visualization import Visualizer

from modules.ResourceManagement import custom_distance

TIME_PERIOD = 24 * 60 * 60 * 100

class Simulation(object):

    def __init__(self, env):

        self.__env = env
        self.__queue = EventQueue(self.__env)

        # Deploying X applictions
        #arrival_times = [int(time) for time in np.random.uniform(0, TIME_PERIOD, env.config.number_of_applications)]

        arrival_times = [int(time) for time in np.cumsum(np.random.poisson(1/(self.__env.config.number_of_applications/TIME_PERIOD), self.__env.config.number_of_applications))]

        time.sleep(1)

        for i in range(self.__env.config.number_of_applications):
            # Generating 1 random application
            application = Application()
            application.randomAppInit()
            application.setAppID(i)
            if self.__env.config.app_duration != 0:
                application.setAppDuration(self.__env.config.app_duration)

            # Getting a random device starting point
            device_id = random.choice(range(len(self.__env.devices)))

            # Creating a placement event
            Placement("Placement",self.__queue, application, device_id, event_time=arrival_times[i]).add_to_queue()

        # Final reporting event

        FinalReport("Final Report", self.__queue, event_time=TIME_PERIOD).add_to_queue()

        # Init devices and network here ?


    def simulate(self):
        # main loop of the simulation

        current_event = None

        print("\nRunning The Event Queue")
        progress_bar = tqdm(total=TIME_PERIOD)

        previous_time=0

        time.sleep(1)

        while not isinstance(current_event,FinalReport):

            event_time, event_index, current_event = self.__queue.pop()

            progress_bar.update(event_time-previous_time)

            self.__env.current_time = event_time

            process_event = current_event.process(self.__env)
            logging.debug("process_event: {}".format(process_event))

            previous_time = event_time

        time.sleep(1)

        visu = Visualizer()

        visu.visualize_environment(self.__env)
        visu.final_results(self.__env)

        logging.info("\n***************\nEND OF SIMULATION\n***************")

'''
# Now, we can play with deployments
def simulate_deployments(env):
    """
    Simulates a complete deployment.
    Simulates 200 successive application deployments.

    Args:
        env : environment

    Returns:
        None
    """
    testings = 200

    event_queue = EventQueue(env)

    for i in range(testings):
        trivial = 0
        application = Application()
        application.randomAppInit()
        application.setAppID(i)

        device_id = random.choice(range(len(env.devices)))

        placement_event = Placement("Placement",event_queue, application, device_id)

        latency, deployed_onto_devices = placement_event.process(env)

        if deployed_onto_devices:
            deployment_event = Deploy("Deployment", event_queue, application, deployed_onto_devices)

            deployment_event.process(env)
            logging.info(f"Deployment success")
            logging.info(f"application {application.id} successfully deployed")
            for i in range(len(application.processus_list)):
                logging.info(f"Deploying processus {application.processus_list[i].id} on device {deployed_onto_devices[i]}")
        else:
            logging.error(f"\nDeployment failure for application {application.id}")


'''
"""


    latency_array = [0]
    operational_latency_array = [0]
    app_refused_array = [0]
    app_success_array = [0]
    proc_success_array = [0]
    trivial_array = [0]

        # deploy on device, get associated deployed status and latency
        success, latency, operational_latency, deployed_onto_devices = application_deploy(application, devices_list[device_id], devices_list, physical_network_link_list)

        latency_array.append(latency_array[-1]+latency)
        operational_latency_array.append(operational_latency_array[-1]+operational_latency)

        if application.num_procs !=1 and len(set(deployed_onto_devices)) == 1:
            trivial = 1

        trivial_array.append(trivial_array[-1]+trivial)

        if success:
            app_success_array.append(app_success_array[-1]+1)
            app_refused_array.append(app_refused_array[-1])
            proc_success_array.append(proc_success_array[-1]+len(deployed_onto_devices))

        else:
            app_success_array.append(app_success_array[-1])
            app_refused_array.append(app_refused_array[-1]+1)
            proc_success_array.append(proc_success_array[-1])



    fig = plt.figure(figsize=(10, 10))
    ax1 = fig.add_subplot()

    ax1.set_ylabel('latency')
    ax1.plot(latency_array, label = 'Deployment Latency', color = 'b')
    ax1.plot(operational_latency_array, label = 'Operational latency', color = 'c')
    ax1.legend()

    ax2 = ax1.twinx()
    ax2.set_ylabel('# of apps (deployed or refused)')
    ax2.set_ylim(0,300)
    ax2.plot(proc_success_array, label = 'Successful processus deployments', color = 'g')
    ax2.plot(app_success_array, label = 'Successful application deploy', color = 'orange')
    ax2.plot(app_refused_array, label = 'Failed application deploy', color = 'r')
    ax2.plot(trivial_array, label = 'Trivial application deploy', color = 'black')
    ax2.legend()

    # Set the labels
    # Title
    ax1.set_title(f'Deployment results')

    # Print the graph
    plt.savefig("fig/results.png")

"""
