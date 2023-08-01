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
    parser.add_argument('--date',
                        help='Date Folder Name',
                        default='today/')
    parser.add_argument('--devices',
                        help='JSON file containing device list',
                        default="latest/devices.json")
    parser.add_argument('--applications',
                        help='JSON file containing application list',
                        default="latest/applications.json")
    parser.add_argument('--arrivals',
                        help='JSON file containing application arrivals list',
                        default="latest/placements.json")
    parser.add_argument('--results',
                        help='results file',
                        default='latest/results.csv')
    options = parser.parse_args()

    return options

def main():

    options = parse_args()

    # Export figure to {ROOT}/data/{date_string}/devices.png
    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting data to {options.date}/ folder")
    os.makedirs(os.path.dirname(options.date), exist_ok=True)
    shutil.copyfile(f"{options.devices}", f"{options.date}/devices.json")
    shutil.copyfile(f"{options.applications}", f"{options.date}/applications.json")
    shutil.copyfile(f"{options.arrivals}", f"{options.date}/placements.json")
    shutil.copyfile(f"{options.results}", f"{options.date}/results.csv")

if __name__ == '__main__':
    logger.info("MAIN")
    main()