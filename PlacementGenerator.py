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
import numpy as np
from tqdm import tqdm
import random
import json

logger = logging.getLogger(__name__)

ROOT = "."

def parse_args():
    parser = argparse.ArgumentParser(description='Process the processing algorithm\'s input')
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
    parser.add_argument('--output',
                        help='output file',
                        default='latest/placements.json')
    options = parser.parse_args()

    return options


def main():

    options = parse_args()

    environment = Environment()

    config = Config(options=options)

    environment.config = config

    time = 0
    arrival_times = []
    rng = np.random.default_rng(seed=environment.config.random_seed)

    #"""
    ### Default
    for _ in range(environment.config.number_of_applications):
        lam = 1/(environment.config.number_of_applications/environment.TIME_PERIOD)
        time+=int(rng.poisson(lam))
        arrival_times.append(time)
    #"""

    """
    ### 9-17
    for _ in range(environment.config.number_of_applications):
        if time < (9 * environment.TIME_PERIOD)/24 or time > (17 * environment.TIME_PERIOD)/24:
            lam = 8/3 * 1/(environment.config.number_of_applications/environment.TIME_PERIOD)
        else:
            lam = 4/9 * 1/(environment.config.number_of_applications/environment.TIME_PERIOD)
        time+=int(rng.poisson(lam))
        arrival_times.append(time)
    """

    """
    ### Lunch Break
    for _ in range(environment.config.number_of_applications):
        if time < (8 * environment.TIME_PERIOD)/24 or time > (18 * environment.TIME_PERIOD)/24:
            lam = 8/3 * 1/(environment.config.number_of_applications/environment.TIME_PERIOD)
        elif time > (12 * environment.TIME_PERIOD)/24 and time < (14 * environment.TIME_PERIOD)/24:
            lam = 8/3 * 1/(environment.config.number_of_applications/environment.TIME_PERIOD)
        else:
            lam = 4/9 * 1/(environment.config.number_of_applications/environment.TIME_PERIOD)
        time+=int(rng.poisson(lam))
        arrival_times.append(time)
    """
    
    date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":","-")[:-1]+"0"

    placement_list = []

    # Exporting placements list
    print("Generating placement dataset")
    logging.info(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Generating dataset")

    random.seed(environment.config.random_seed)

    for i in tqdm(range(environment.config.number_of_applications)):
        placement = dict()
        placement["placement_time"] = arrival_times[i]
        placement["requesting_device"] = random.choice(range(environment.config.number_of_devices))
        placement["application"] = i
        placement_list.append(placement)
    print("Exporting data")

    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}:Exporting data to {options.output}")
    os.makedirs(os.path.dirname(options.output), exist_ok=True)

    environment.export_applications(filename=f"{options.output}")

    json_string = json.dumps(placement_list, indent=4)
    with open(f"{options.output}", 'w') as file:
        file.write(json_string)

if __name__ == '__main__':
    logger.info("MAIN")
    main()