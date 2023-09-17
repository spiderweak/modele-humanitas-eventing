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
from modules.events.Event import (Event, Placement, Deploy_Proc, Sync, FinalReport)
from modules.Visualization import Visualizer

from modules.ResourceManagement import custom_distance

import json

TIME_PERIOD = 24 * 60 * 60 * 100

class Simulation(object):

    def __init__(self, env):

        self.__env = env
        self.__queue = EventQueue(self.__env)

        # Deploying X applictions
        #arrival_times = [int(time) for time in np.random.uniform(0, TIME_PERIOD, env.config.number_of_applications)]


    def initSimulation(self):

        arrival_times = [int(time) for time in np.cumsum(np.random.poisson(1/(self.__env.config.number_of_applications/TIME_PERIOD), self.__env.config.number_of_applications))]

        time.sleep(1)

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

        logging.info("\n***************\nEND OF SIMULATION\n***************")

    def full_state_simulate(self):
        # alt loop of the simulation

        current_event = None

        print("\nRunning The Event Queue")
        progress_bar = tqdm(total=TIME_PERIOD)

        previous_time=0

        time.sleep(1)

        while not isinstance(current_event,FinalReport):

            event_time, event_index, current_event = self.__queue.pop()

            progress_bar.update(event_time-previous_time)

            self.__env.current_time = event_time

            if event_time != previous_time:
                self.__env.extractDevicesResources()
                self.__env.extractCurrentlyDeployedAppData()

            process_event = current_event.process(self.__env)
            logging.debug("process_event: {}".format(process_event))

            previous_time = event_time

        time.sleep(1)

        logging.info("\n***************\nEND OF SIMULATION\n***************")



    def importQueueItems(self):
        try:
            with open(self.__env.config.arrivals_file) as file:
                arrivals_list = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Please add placements list in argument, default value is placements.json in current directory")

        for item in arrivals_list:
            application = self.__env.getApplicationByID(item["application"])
            device_id = item["requesting_device"]
            arrival_time = item["placement_time"]
            Placement("Placement",self.__queue, application, device_id, event_time=arrival_time).add_to_queue()

        FinalReport("Final Report", self.__queue, event_time=TIME_PERIOD).add_to_queue()