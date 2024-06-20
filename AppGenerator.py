#!/usr/bin/env python3
"""
The AppGenerator Module performs a complete deployment test on 200 applications over 40 devices.

Usage::

    python3 AppGenerator.py
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
    """
    Parses command line arguments for the application generator.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Process the processing algorithm's input")
    parser.add_argument('--config',
                        help='Configuration file',
                        default='config.yaml')
    parser.add_argument('--output',
                        help='Output file',
                        default='latest/applications.json')
    options = parser.parse_args()
    return options

def main():
    """
    Main function to run the application generator.

    This function parses command line arguments, loads configuration,
    generates application lists, and exports the applications to the specified output file.
    """
    options = parse_args()

    environment = Environment()
    config = Config(options=options)
    environment.config = config

    environment.generate_application_list()

    logging.debug(f"{datetime.datetime.now().isoformat(timespec='minutes')}: Exporting data to {options.output}")
    os.makedirs(os.path.dirname(options.output), exist_ok=True)

    environment.export_applications(filename=options.output)

if __name__ == '__main__':
    logger.info("MAIN")
    main()
