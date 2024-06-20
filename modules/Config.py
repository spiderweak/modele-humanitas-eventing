"""
Config Module

This module handles the configuration settings for the application.
It initializes default values, loads configurations from a YAML file,
and sets options based on command-line arguments and YAML configuration.

Classes:
    Config: Manages the application's configuration settings.

Usage Example:
    config = Config(options=args)
"""

import yaml
import logging
import os
from typing import Any, Dict, Union

import argparse

import random

class Config:
    """
    Manages the application's configuration settings.

    Attributes:
        parsed_yaml (Dict[str, Any]): The parsed YAML configuration.
        log_level (int): Logging level.
        log_filename (str): Name of the log file.
        devices_template_filename (str): Filename for device templates.
        application_template_filename (str): Filename for application templates.
        results_filename (str): Filename for results.
        number_of_applications (int): Number of applications.
        number_of_devices (int): Number of devices.
        wifi_range (float): WiFi range.
        app_duration (int): Application duration.
        k_param (int): Parameter for routing.
        _3D_space (Dict[str, Union[int, float]]): Space dimensions.
        random_seed (int): Random seed value.
    """
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_LOG_FILENAME: str = 'log.txt'
    DEFAULT_DEVICES_TEMPLATE_FILENAME: str = 'devices.json'
    DEFAULT_APPLICATION_TEMPLATE_FILENAME: str = 'application.json'
    DEFAULT_RESULTS_FILENAME: str = 'results.json'
    DEFAULT_NUMBER_OF_APPLICATIONS: int = 500
    DEFAULT_NUMBER_OF_DEVICES: int = 40
    DEFAULT_WIFI_RANGE: float = 6.0
    DEFAULT_APP_DURATION: int = 0
    DEFAULT_K_PARAM: int = 10
    DEFAULT_3D_SPACE: Dict[str, Union[int, float]] = {"x_min": 0, "x_max": 40, "y_min": 0, "y_max": 40, "z_min": 0, "z_max": 0}

    RANDOM_SEED_VALUE = int(100 * rendom.random())

    def __init__(self, *, options: argparse.Namespace):
        """
        Initializes the application configuration with default values or values from a YAML file.

        :param options: Parsed command-line options.
        :type options: argparse.Namespace
        """
        self.set_defaults()

        if hasattr(options, 'config'):
            self.load_yaml(options.config)
        else:
            logging.error("config option not used, using default settings.")

        self.setup_logging(options)
        self.set_options(options)

    def set_defaults(self) -> None:
        """Sets default values for all attributes."""
        self.parsed_yaml: Dict[str, Any] = {}
        self.log_level: int = self.DEFAULT_LOG_LEVEL
        self.log_filename: str = self.DEFAULT_LOG_FILENAME

        self.devices_template_filename: str = self.DEFAULT_DEVICES_TEMPLATE_FILENAME
        self.application_template_filename: str = self.DEFAULT_APPLICATION_TEMPLATE_FILENAME
        self.results_filename: str = self.DEFAULT_RESULTS_FILENAME

        self.number_of_applications: int = self.DEFAULT_NUMBER_OF_APPLICATIONS
        self.number_of_devices: int = self.DEFAULT_NUMBER_OF_DEVICES
        self.wifi_range: float = self.DEFAULT_WIFI_RANGE

        self._3D_space: Dict[str, Union[int, float]] = self.DEFAULT_3D_SPACE

        self.k_param: int = self.DEFAULT_K_PARAM

        self.app_duration: int = self.DEFAULT_APP_DURATION

        self.random_seed: int = self.RANDOM_SEED_VALUE

    def load_yaml(self, config_file_path: str) -> None:
        """
        Loads settings from a YAML file.

        :param config_file_path: Configuration file path.
        :type config_file_path: str
        """
        try:
            with open(config_file_path, 'r') as config_file:
                self.parsed_yaml = yaml.safe_load(config_file)
        except FileNotFoundError:
            logging.error("Configuration File Not Found, using default settings.")

    def setup_logging(self, options: argparse.Namespace) -> None:
        """
        Initializes logging based on parsed YAML.

        :param options: Parsed command-line options.
        :type options: argparse.Namespace
        """
        try:
            match self.parsed_yaml.get('loglevel', 'info'):
                case 'error':
                    self.log_level = logging.ERROR
                case 'warning':
                    self.log_level = logging.WARNING
                case 'info':
                    self.log_level = logging.INFO
                case 'debug':
                    self.log_level = logging.DEBUG
                case _:
                    self.log_level = logging.INFO
        except (KeyError, TypeError):
            self.log_level = logging.INFO

        self.log_filename = getattr(options, 'logs', self.parsed_yaml.get('logfile', 'log.txt'))

        try:
            os.makedirs(os.path.dirname(self.log_filename), exist_ok=True)
        except FileNotFoundError:
            if os.path.dirname(self.log_filename):
                raise

        logging.basicConfig(filename=self.log_filename, encoding='utf-8', level=self.log_level)
        logging.info('\n')

    def _set_attribute_from_yaml(self, attr_name: str, yaml_path: list, value_type: type) -> None:
        """
        Helper function to set attribute from parsed YAML.

        :param attr_name: The name of the attribute to set.
        :type attr_name: str
        :param yaml_path: The list of keys to navigate the YAML dictionary.
        :type yaml_path: list
        :param value_type: The type to cast the value to (e.g., int, float, str).
        :type value_type: type
        """
        try:
            value = self.parsed_yaml
            for key in yaml_path:
                value = value[key]
            setattr(self, attr_name, value_type(value))
        except (KeyError, TypeError) as e:
            logging.error(f"Config Error, Default simulation value {getattr(self, attr_name)} used for entry {e}")

    def set_options(self, options: argparse.Namespace) -> None:
        """
        Sets other options based on parsed YAML and command-line options.

        :param options: Parsed command-line options.
        :type options: argparse.Namespace
        """
        self._set_attribute_from_yaml('number_of_applications', ['application_number'], int)
        self._set_attribute_from_yaml('number_of_devices', ['device_number'], int)
        self._set_attribute_from_yaml('wifi_range', ['wifi_range'], float)

        for boundary in self._3D_space.keys():
            self._set_attribute_from_yaml(f'_3D_space["{boundary}"]', ['device_positioning', boundary], float)

        self._set_attribute_from_yaml('k_param', ['k_param'], int)
        self._set_attribute_from_yaml('app_duration', ['app_duration'], float)
        self._set_attribute_from_yaml('random_seed', ['seed'], int)

        # Setting options
        try:
            self.results_filename = options.output
        except (KeyError, AttributeError) as e:
            logging.error(f"{e}, processing output will be default {self.results_filename}")

        self.results_filename = getattr(options, 'results', self.results_filename)
        self.output_folder = os.path.dirname(self.results_filename)

        self.devices_file = getattr(options, 'devices', None)
        self.applications_file = getattr(options, 'applications', None)
        self.arrivals_file = getattr(options, 'arrivals', None)
        self.dry_run = getattr(options, 'dry_run', False)
