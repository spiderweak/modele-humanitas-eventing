#!/usr/bin/env python3
"""
Does a complete deployment test on 200 applications over 40 devices

Usage:

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
    parser = argparse.ArgumentParser(description='Process the processing algorithm\'s input')
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
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

    # Exporting devices list
    print("Generating dataset and exporting data")
    logging.info(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Generating dataset and exporting data")
    date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":","-")[:-1]+"0"
    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting data to {ROOT}data/{date_string}/devices.json")

    try :
        os.makedirs(f"{ROOT}/data/{date_string}")
    except FileExistsError:
        pass

    environment.export_devices(filename=f"{ROOT}/data/{date_string}/devices.json")

    # Export figure to {ROOT}/data/{date_string}/devices.png
    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting figure to {ROOT}/data/{date_string}/devices.png")
    shutil.copyfile(f"{ROOT}/fig/graph.png", f"{ROOT}/data/{date_string}/devices.png")

if __name__ == '__main__':
    logger.info("MAIN")
    main()