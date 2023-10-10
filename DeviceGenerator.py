#!/usr/bin/env python3
"""
The DeviceGenerator Module generates a list of devices based on the information in the config file : Number of devices, their positions, their resources, etc.

Links are established either using proximity, extrapolating from possible Wi-Fi connectivity between devices, or from the information provided in the input files.

It then generates a Routing Table for shortest single path between each devices based on the links between them.

Finally, information is exported to an output folder, defaults to *latest/devices.json*


Usage::

    python3 DeviceGenerator.py

"""

from modules.Config import Config
from modules.resource.Device import Device
from modules.Environment import Environment

import argparse
import os
import datetime

import logging
import shutil

logger = logging.getLogger(__name__)

ROOT = "."

def parse_args():
    """
        Parses the arguments from the configuration, and generates a --help subcommand to assist user
    """

    parser = argparse.ArgumentParser(description='Process the processing algorithm\'s input')
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
    parser.add_argument('--output',
                        help='output file',
                        default='latest/devices.json')
    options = parser.parse_args()

    return options

def main():
    """
        Runs the core loop for the program, loads the configuration after a call to the argument parser, generates the devices, output to destination file, logs all operations
    """

    options = parse_args()

    environment = Environment()

    config = Config(options=options)

    environment.config = config

    environment.generate_device_list()
    environment.import_links()

    environment.process_closeness_centrality()

    environment.plot_device_network()
    environment.generate_routing_table()

    # Exporting devices list
    print("Generating dataset and exporting data")

    logging.info(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting data to {options.output}")
    os.makedirs(os.path.dirname(options.output), exist_ok=True)

    environment.export_devices(filename=f"{options.output}")

    date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":","-")[:-1]+"0"

    # Export figure to {ROOT}/data/{date_string}/devices.png
    logging.info(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting figure to {ROOT}/data/{date_string}/devices.png")
    os.makedirs(os.path.dirname(f"{ROOT}/data/{date_string}/devices.png"), exist_ok=True)
    shutil.copyfile(f"{ROOT}/fig/graph.png", f"{ROOT}/data/{date_string}/devices.png")
    shutil.copyfile(f"{ROOT}/fig/graph.png", f"{ROOT}/latest/devices.png")

if __name__ == '__main__':
    logger.info("MAIN")
    main()