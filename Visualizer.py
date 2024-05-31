#!/usr/bin/env python3
"""
The Visualize Module performs a complete deployment test on 200 applications over 40 devices.

Usage::

    python3 Visualize.py
"""

from modules.Config import Config
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
    Parses the arguments from the configuration and generates a --help subcommand to assist the user.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Process the processing algorithm's input")
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
    parser.add_argument('--results',
                        help='Results file to process',
                        default='results.json')
    options = parser.parse_args()
    return options

def main():
    """
    Runs the core loop for the program: loads the configuration after a call to the argument parser, imports the results, and generates visualizations.
    """
    options = parse_args()

    environment = Environment()
    config = Config(options=options)
    environment.config = config

    environment.import_results()

    visu = Visualizer()
    visu.other_final_results(environment)

    # Uncomment the following lines if exporting data is needed
    # logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}: Exporting data to {options.output}")
    # shutil.copyfile("results.csv", f"{options.output}")

if __name__ == '__main__':
    logger.info("MAIN")
    main()
