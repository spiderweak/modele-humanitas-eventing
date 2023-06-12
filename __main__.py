#!/usr/bin/env python3
"""
Does a complete deployment test on 200 applications over 40 devices

Usage:

    python3 main.py

"""

from modules.Config import Config

from modules.resource.Application import Application
from modules.resource.Device import Device
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Processus import Processus
from modules.resource.Path import Path
from modules.EventQueue import EventQueue
from modules.Environment import Environment
from modules.Event import (Event, Placement, Deploy)


from modules.Simulation import Simulation

import argparse
import yaml
import random

import logging

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Process the processing algorithm\'s input')
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
    parser.add_argument('--simulate',
                        help='Boolean, default to False, run simulator if true',
                        default=True)
    parser.add_argument('--scratchdevicedb',
                        help='Boolean, default to False, archives device database before runnning',
                        default=False)
    options = parser.parse_args()

    return options

def main():

    options = parse_args()

    environment = Environment()

    config = Config(options, environment)

    environment.setConfig(config)
    environment.generate_routing_table()

    if options.simulate:

        logging.info("Running complete simulation")
        simulation = Simulation(environment)
        simulation.simulate()

    else:
        logging.info("Testing a single app deployment")

        current_device_id = random.randint(0, len(environment.devices)-1)
        my_application = Application()

        event_queue = EventQueue(environment)

        with open(options.application, 'r') as app_config:

            app_yaml = yaml.safe_load(app_config)
            my_application.app_yaml_parser(app_yaml)

            Placement("Placement", event_queue, my_application, current_device_id).add_to_queue()

            current_event = None

            while not event_queue.is_empty():
                event_time, event_index, current_event = event_queue.pop()

                process_event = current_event.process(environment)

                logging.debug("process_event: {}".format(process_event))

            logging.info("\n***************\nEND OF TEST\n***************")

if __name__ == '__main__':
    logger.info("MAIN")
    main()