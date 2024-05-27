#!/usr/bin/env python3
"""
The PlacementGenerator Module performs a complete deployment test on 200 applications over 40 devices.

Usage:
    python3 PlacementGenerator.py
"""

from modules.Config import Config
from modules.Environment import Environment

import argparse
import os
import datetime
import logging
import numpy as np
from tqdm import tqdm
import random
import json

logger = logging.getLogger(__name__)

ROOT = "."

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
    parser.add_argument('--output',
                        help='Output file',
                        default='latest/placements.json')
    options = parser.parse_args()
    return options

def main():
    """
    Runs the core loop for the program: loads the configuration after a call to the argument parser, generates the placements, outputs to the destination file, and logs all operations.
    """
    options = parse_args()

    environment = Environment()
    config = Config(options=options)
    environment.config = config

    time = 0
    arrival_times = []
    rng = np.random.default_rng(seed=environment.config.random_seed)

    # Generate arrival times for applications
    for _ in range(environment.config.number_of_applications):
        lam = 1 / (environment.config.number_of_applications / environment.TIME_PERIOD)
        time += int(rng.poisson(lam))
        arrival_times.append(time)

    placement_list = []

    # Exporting placements list
    print("Generating placement dataset")
    logging.info(f"{datetime.datetime.now().isoformat(timespec='minutes')}: Generating dataset")

    random.seed(environment.config.random_seed)

    for i in tqdm(range(environment.config.number_of_applications)):
        placement = dict()
        placement["placement_time"] = arrival_times[i]
        placement["requesting_device"] = random.choice(range(environment.config.number_of_devices))
        placement["application"] = i
        placement_list.append(placement)

    print("Exporting data")
    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}: Exporting data to {options.output}")
    os.makedirs(os.path.dirname(options.output), exist_ok=True)

    environment.export_applications(filename=options.output)

    json_string = json.dumps(placement_list, indent=4)
    with open(options.output, 'w') as file:
        file.write(json_string)

if __name__ == '__main__':
    logger.info("MAIN")
    main()
