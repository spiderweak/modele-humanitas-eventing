"""
Simulation Module

This module provides the Simulation class for managing the simulation process.
It handles the initialization, event processing, and final reporting of the simulation.
The simulation involves generating applications, placing them on devices, and recording
the results.

Classes:
    Simulation: Manages the simulation process.

Usage Example:
    env = Environment(config)
    simulation = Simulation(env)
    simulation.init_simulation() # Optional
    simulation.simulate()
"""

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
from modules.Environment import Environment
from modules.EventQueue import EventQueue

from modules.events.Placement import Placement
from modules.events.Organize import Organize
from modules.events.PlacementAlt import PlacementAlt, BatchProcessing
from modules.events.FinalReport import FinalReport

from modules.Visualization import Visualizer

from modules.ResourceManagement import custom_distance

import json

TIME_PERIOD = 24 * 60 * 60 * 100
BATCH_STEP = 5 * 60 * 100

class Simulation(object):
    """
    Simulation class to manage the simulation process.

    :param env: The simulation environment.
    :type env: Environment
    """
    def __init__(self, env):
        """
        Initializes the Simulation instance.

        :param env: The simulation environment.
        :type env: Environment
        """
        self.__env: Environment = env
        self.__queue = EventQueue(self.__env)

        # Deploying X applictions
        #arrival_times = [int(time) for time in np.random.uniform(0, TIME_PERIOD, env.config.number_of_applications)]

    def init_simulation(self):
        """
        Initializes the simulation by generating arrival times and events.
        """
        if self.__env.config is None:
            raise ValueError

        arrival_times = [int(time) for time in np.cumsum(np.random.poisson(1/(self.__env.config.number_of_applications/TIME_PERIOD), self.__env.config.number_of_applications))]

        time.sleep(1)

        for i in tqdm(range(self.__env.config.number_of_applications)):
            # Generating 1 random application
            application = Application()
            application.random_app_init()
            application.id = i
            if self.__env.config.app_duration != 0:
                application.set_app_duration(self.__env.config.app_duration)

            # Getting a random device starting point
            device_id = random.choice(range(len(self.__env.devices)))

            # Creating a placement event
            Placement("Placement", self.__queue, application, device_id, event_time=arrival_times[i]).add_to_queue()
        # Final reporting event

        FinalReport("Final Report", self.__queue, event_time=TIME_PERIOD).add_to_queue()

    def simulate(self):
        """
        Main loop of the simulation.
        """
        current_event = None

        print("\nRunning The Event Queue")
        progress_bar = tqdm(total=TIME_PERIOD)

        previous_time=0

        while not isinstance(current_event,FinalReport):

            event_time, event_index, current_event = self.__queue.pop()

            progress_bar.update(event_time-previous_time)

            self.__env.current_time = event_time

            process_event = current_event.process(self.__env)
            logging.debug(f"process_event: {process_event}")

            previous_time = event_time

        logging.info("\n**********\nEND OF SIMULATION\n**********")

    def full_state_simulate(self):
        """
        Alternate loop of the simulation.
        """
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
                self.__env.extract_devices_resources()
                self.__env.extract_currently_deployed_apps_data()

            process_event = current_event.process(self.__env)
            logging.debug(f"process_event: {process_event}")

            previous_time = event_time

        logging.info("\n**********\nEND OF SIMULATION\n**********")


    def import_queue_items(self):
        """
        Imports queue items from a JSON file.
        """
        if self.__env.config is None:
            raise ValueError

        try:
            with open(self.__env.config.arrivals_file) as file:
                arrivals_list = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Please add placements list in argument, default value is placements.json in current directory")

        try:
            if self.__env.config.batch_enable:

                arrival_time = 0
                batch_counter = 0
                batches: dict[int, BatchProcessing] = dict()

                while arrival_time <= TIME_PERIOD:

                    batch_counter +=1
                    arrival_time = batch_counter * BATCH_STEP

                    batches[batch_counter] = BatchProcessing("BatchProcessing", self.__queue, event_time = arrival_time)
                    batches[batch_counter].add_to_queue()

                next_batch = batches[batch_counter]

                for counter in range(batch_counter-1, 0, -1):
                    batches[counter].next_batch = next_batch
                    next_batch = batches[counter]

                for item in arrivals_list:
                    application = self.__env.get_application_by_id(item["application"])
                    device_id = item["requesting_device"]
                    arrival_time = item["placement_time"]
                    associated_batch_id = int(arrival_time/BATCH_STEP) +1
                    PlacementAlt("Placement", self.__queue, application, device_id, event_time=arrival_time, associated_batch=batches[associated_batch_id]).add_to_queue()
            else:
                for item in arrivals_list:
                    application = self.__env.get_application_by_id(item["application"])
                    device_id = item["requesting_device"]
                    arrival_time = item["placement_time"]
                    Placement("Placement", self.__queue, application, device_id, event_time=arrival_time).add_to_queue()
        except:
            raise

        FinalReport("Final Report", self.__queue, event_time=TIME_PERIOD).add_to_queue()

    def bulk_import_queue_items(self):
        """
        Bulk imports queue items from a JSON file.
        """
        try:
            with open(self.__env.config.arrivals_file) as file:
                arrivals_list = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Please add placements list in argument, default value is placements.json in current directory")

        for item in arrivals_list:
            application = self.__env.get_application_by_id(item["application"])
            arrival_time = item["placement_time"]
            Organize("Organize",self.__queue, application, event_time=arrival_time).add_to_queue()

        FinalReport("Final Report", self.__queue, event_time=TIME_PERIOD).add_to_queue()
