#!/usr/bin/env python3
"""
Does a complete deployment test on 200 applications over 40 devices

Usage:

    python3 DeviceGenerator.py

"""

from modules.Config import Config
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
    parser.add_argument('--output',
                        help='output file',
                        default='latest/applications.json')
    options = parser.parse_args()

    return options

def main():

    options = parse_args()

    environment = Environment()

    config = Config(options=options)

    environment.config = config

    environment.generate_application_list()

    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting data to {options.output}")
    os.makedirs(os.path.dirname(options.output), exist_ok=True)

    environment.export_applications(filename=f"{options.output}")


if __name__ == '__main__':
    logger.info("MAIN")
    main()