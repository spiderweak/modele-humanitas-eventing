#!/usr/bin/env python3
"""
Does a complete deployment test on 200 applications over 40 devices

Usage:

    python3 Visualize.py
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
    parser = argparse.ArgumentParser(description='Process the processing algorithm\'s input')
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
    parser.add_argument('--results',
                        help='results file to process',
                        default='results.json')
    options = parser.parse_args()

    return options

def main():

    options = parse_args()

    environment = Environment()

    config = Config(options=options)

    environment.config = config

    environment.import_results()

    visu = Visualizer()

    visu.final_results(environment)

    #logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting data to {options.output}")
    #shutil.copyfile(f"results.csv", f"{options.output}")


if __name__ == '__main__':
    logger.info("MAIN")
    main()