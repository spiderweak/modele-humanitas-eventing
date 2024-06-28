#!/usr/bin/env python3
"""
Does a complete deployment test on 200 applications over 40 devices

Usage::

    python3 Processing.py

Example::

    python3 Processing.py --devices="$device_file" --applications="$application_file" --arrivals="$placement_file" --output="output/$unique_id/results.json"
"""

from modules.Config import Config

from modules.resource.Application import Application
from modules.resource.Device import Device
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Processus import Processus
from modules.resource.Path import Path
from modules.EventQueue import EventQueue
from modules.Environment import Environment
from modules.Visualization import Visualizer

from modules.Simulation import Simulation

import argparse
import yaml
import random
import os

import logging
import datetime
import shutil

logger = logging.getLogger(__name__)


def parse_args():
    """
    Parses the arguments from the configuration and generates a -help subcommand to assist the user.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description='Process the processing algorithm\'s input')
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
    parser.add_argument('--simulate',
                        help='Boolean, default to False, run simulator if true',
                        default=True)
    parser.add_argument('--dry-run',
                        help='Runs an empty simulation to export data',
                        default=False)
    parser.add_argument('--batch',
                        help='Enables batch mode for placement',
                        default=False)
    parser.add_argument('--devices',
                        help='JSON file containing device list',
                        default="latest/devices.json")
    parser.add_argument('--applications',
                        help='JSON file containing application list',
                        default="latest/applications.json")
    parser.add_argument('--arrivals',
                        help='JSON file containing application arrivals list',
                        default="latest/placement.json")
    parser.add_argument('--output',
                        help='Output file',
                        default='latest/results.json')
    parser.add_argument('--logs',
                        help='Output file',
                        default='latest/logs.txt')
    options = parser.parse_args()

    return options

def main():
    """
    Main function to run the processing module.

    This function parses command line arguments, loads the configuration,
    imports devices and links, runs the simulation, and exports the results.
    """
    options = parse_args()

    environment = Environment()

    config = Config(options=options)
    environment.config = config

    environment.import_devices()
    environment.import_links()

    environment.import_ospf_routing_table()
    # environment.generate_other_routing_table(k_param=10)

    environment.import_applications()

    environment.set_data_max()

    logging.info("Running complete simulation")
    simulation = Simulation(environment)

    simulation.import_queue_items()

    simulation.simulate()

    # Exporting devices list
    print("Generating dataset and exporting data")

    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}: Exporting data to {options.output}")
    os.makedirs(os.path.dirname(options.output), exist_ok=True)

    environment.export_devices(options.output)

    visu = Visualizer()

    visu.visualize_environment(environment)
    visu.apps_visualiser(environment)
    visu.final_results(environment)
    visu.plot_resource_and_application_counts(environment)

if __name__ == '__main__':
    logger.info("MAIN")
    main()
