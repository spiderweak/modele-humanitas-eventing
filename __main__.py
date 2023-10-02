#!/usr/bin/env python3
"""
Does a complete deployment test on 200 applications over 40 devices

Usage:

    python3 main.py

"""

from modules.Config import Config

from modules.resource.Application import Application
from modules.resource.Device import Device
from modules.resource.PhysicalNetworkLink import PhysicalNetworkLink
from modules.resource.Processus import Processus
from modules.resource.Path import Path
from modules.EventQueue import EventQueue
from modules.Environment import Environment
from modules.events.Event import (Event, Placement, Deploy_Proc, Sync)


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
    options = parser.parse_args()

    return options

def main():

    options = parse_args()

    environment = Environment()

    config = Config(options, environment)

    environment.config = config

    environment.generateDeviceList()
    environment.importLinks()
    environment.plotDeviceNetwork()
    environment.generateRoutingTable()

    environment.generateApplicationList()

    if options.simulate:

        logging.info("Running complete simulation")
        simulation = Simulation(environment)

        simulation.initSimulation()

        simulation.simulate()

if __name__ == '__main__':
    logger.info("MAIN")
    main()