#!/usr/bin/env python3
"""
Does a complete deployment test on 200 applications over 40 devices

Usage:

    python3 main.py

"""

from modules.Application import Application
from modules.Device import Device
from modules.PhysicalNetworkLink import PhysicalNetworkLink
from modules.Processus import Processus
from modules.Path import Path
from modules.EventQueue import EventQueue
from modules.Environment import Environment
from modules.Event import (Event, Placement, Deploy)


from modules.db.interact_db import create_db
from modules.db.interact_db import populate_db
from modules.db.interact_db import dump_from_db

from modules.Simulation import Simulation
from modules.Simulation import generate_and_plot_devices_positions

import argparse
import yaml
import random
import os.path

import logging
import datetime



# GLOBAL VARIABLES (bad practice)
N_DEVICES = 40

## Setting the wifi range
#wifi_range = 6

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description='Process the processing algorithm\' input')
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
    parser.add_argument('--simulate',
                        help='Boolean, default to False, run simulator if true',
                        default=True)
    parser.add_argument('--application',
                        help='yaml application descriptor',
                        default='app.yaml')
    parser.add_argument('--scratchdevicedb',
                        help='Boolean, default to False, archives device database before runnning',
                        default=False)
    options = parser.parse_args()

    return options

def main():

    options = parse_args()

    with open(options.config, 'r') as config_file:
        parsed_yaml = yaml.safe_load(config_file)

    # Log level
    try:
        match parsed_yaml['loglevel']:
            case 'error':
                loglevel = logging.ERROR
            case 'warning':
                loglevel = logging.WARNING
            case 'info':
                loglevel = logging.INFO
            case 'debug':
                loglevel = logging.DEBUG
            case _:
                loglevel = logging.INFO
    except KeyError:
        loglevel = logging.INFO

    # Log file
    try:
        logfilename = parsed_yaml['logfile']
    except KeyError:
        logfilename = 'log.txt'

    logging.basicConfig(filename=logfilename, encoding='utf-8', level=loglevel)

    logging.info('\n')

    if options.scratchdevicedb:
        date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":","-")
        if os.path.isfile(parsed_yaml['database_url']['device']):
            os.rename(parsed_yaml['database_url']['device'], f"modules/db/archives/{parsed_yaml['database_url']['device']}-{date_string}")

    if not os.path.isfile(parsed_yaml['database_url']['device']):
        logging.info("Generating random device positions")
        devices = list()
        generate_and_plot_devices_positions(devices)
        create_db(parsed_yaml['database_url']['device'])
        populate_db(devices, parsed_yaml['database_url']['device'])

    logging.info("Generating simulation environment")
    environment = Environment()

    dump_from_db(environment, parsed_yaml['database_url']['device'])

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