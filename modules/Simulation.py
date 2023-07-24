import matplotlib.pyplot as plt
import networkx as nx
import random
import logging

import time
import datetime
import os

import numpy as np

from tqdm import tqdm

from modules.resource.Application import Application
from modules.EventQueue import EventQueue
from modules.Event import (Event, Placement, Deploy_Proc, Sync, FinalReport)
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

        date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":","-")[:-1]+"0"

        # Exporting devices list
        print("Generating dataset and exporting data")
        os.makedirs(f"data/{date_string}")
        env.export_devices(filename=f"data/{date_string}/devices.json")

        for i in tqdm(range(self.__env.config.number_of_applications)):
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

        self.__queue.export(filename=f"data/{date_string}/placement.json")

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
