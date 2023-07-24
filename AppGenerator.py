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
    options = parser.parse_args()

    return options

def main():

    options = parse_args()

    environment = Environment()

    config = Config(options, environment)

    environment.setConfig(config)

    environment.generateApplicationList()

    # Exporting applications list
    print("Generating application dataset and exporting data")
    date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":","-")[:-1]+"0"
    logging.info(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Generating application dataset and exporting data")

    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting data to {ROOT}/data/{date_string}/applications.json")
    try :
        os.makedirs(f"{ROOT}/data/{date_string}")
    except FileExistsError:
        pass

    environment.export_applications(filename=f"{ROOT}/data/{date_string}/applications.json")


if __name__ == '__main__':
    logger.info("MAIN")
    main()