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

from simulation import generate_and_plot_devices_positions
from simulation import generate_routing_table
from simulation import simulate_deployments

import argparse
import yaml
import random
import os.path

import logging



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
                        default=False)
    parser.add_argument('--application',
                        help='yaml application descriptor',
                        default='app.yaml')

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

    devices = list()
    devices_list = []

    generate_and_plot_devices_positions(devices)

    if not os.path.isfile(parsed_yaml['database_url']['device']):
        create_db(parsed_yaml['database_url']['device'])
        populate_db(devices, parsed_yaml['database_url']['device'])

    dump_from_db(devices_list, parsed_yaml['database_url']['device'])

    physical_network_link_list = [0]*len(devices_list)*len(devices_list)
    generate_routing_table(devices_list, physical_network_link_list)

    environment = Environment()

    if options.simulate:

        simulate_deployments(devices_list, physical_network_link_list)

        return 0,1

    else:
        current_device_id = random.randint(0, len(devices_list)-1)
        my_application = Application()

        event_queue = EventQueue(environment)
        placement_event = Placement("Placement",event_queue)

        deployment_event = Deploy("Deployment", event_queue)


        with open(options.application, 'r') as app_config:

            app_yaml = yaml.safe_load(app_config)
            my_application.app_yaml_parser(app_yaml)


            deployed_onto_devices = placement_event.process(my_application, devices_list[current_device_id], devices_list, physical_network_link_list)

            if deployed_onto_devices:
                deployment_event.process(my_application, deployed_onto_devices, devices_list, physical_network_link_list)
                logging.info(f"Deployment success")
                logging.info(f"application {my_application.id} successfully deployed")
                for i in range(len(my_application.processus_list)):
                    logging.info(f"Deploying processus {my_application.processus_list[i].id} on device {deployed_onto_devices[i]}")
            else:
                logging.error(f"\nDeployment failure for application {my_application.id}")

        return deployed_onto_devices



if __name__ == '__main__':
    logger.info("MAIN")
    main()