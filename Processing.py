#!/usr/bin/env python3
"""
Does a complete deployment test on 200 applications over 40 devices

Usage:

    python3 Processing.py
"""

from modules.Config import Config

from modules.resource.Application import Application
from modules.resource.Device import Device
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Processus import Processus
from modules.resource.Path import Path
from modules.EventQueue import EventQueue
from modules.Environment import Environment
from modules.Event import (Event, Placement, Deploy_Proc, Sync)


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
    parser.add_argument('--devices',
                        help='JSON file containing device list',
                        default="devices.json")
    parser.add_argument('--applications',
                        help='JSON file containing application list',
                        default="applications.json")
    parser.add_argument('--arrivals',
                        help='JSON file containing application arrivals list',
                        default="placements.json")
    options = parser.parse_args()

    return options

def main():

    options = parse_args()

    environment = Environment()

    config = Config(options, environment)

    environment.setConfig(config)
    environment.importDevices() # Conflict between importDevices and setConfig, will need to fix this at one point

    environment.importApplications()

    logging.info("Running complete simulation")
    simulation = Simulation(environment)

    simulation.importQueueItems()

    simulation.simulate()

if __name__ == '__main__':
    logger.info("MAIN")
    main()