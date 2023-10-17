import yaml
import logging
from typing import Any, Dict, Union

import argparse

class Config:
    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_LOG_FILENAME: str = 'log.txt'
    DEFAULT_DEVICES_TEMPLATE_FILENAME: str = 'devices.json'
    DEFAULT_APPLICATION_TEMPLATE_FILENAME: str = 'application.json'
    DEFAULT_RESULTS_FILENAME: str = 'results.json'
    DEFAULT_NUMBER_OF_APPLICATIONS: int = 500
    DEFAULT_NUMBER_OF_DEVICES: int = 40
    DEFAULT_WIFI_RANGE: float = 6.0
    DEFAULT_APP_DURATION: int = 0
    DEFAULT_3D_SPACE: Dict[str,Union[int,float]] = {"x_min": 0, "x_max": 40, "y_min": 0, "y_max": 40, "z_min": 0, "z_max": 0}

    def __init__(self, *, options: argparse.Namespace):
        """Initializes the application configuration with default values or values from a YAML file.

        Args:
            options (argparse.Namespace): parsed command-line options
            env (Environment): simulation environment

        Attributes:
            parsed_yaml (Dict[str, Any]): Contains the parsed configuration YAML file, stored as a dict.
            log_level (int): Integer representation of the parsed log level.
            log_filename (str): Log file name.
            ... (and others)
        """
        self.set_defaults()

        if hasattr(options, 'config'):
            self.load_yaml(options.config)
        else:
            logging.error("config option not used, using default settings.")

        self.setup_logging()
        self.set_options(options)

    def set_defaults(self) -> None:
        """Sets default values for all attributes."""
        self.parsed_yaml: Dict[str, Any] = {}
        self.log_level : int = self.DEFAULT_LOG_LEVEL
        self.log_filename: str = self.DEFAULT_LOG_FILENAME


        self.devices_template_filename: str = self.DEFAULT_DEVICES_TEMPLATE_FILENAME
        self.application_template_filename: str = self.DEFAULT_APPLICATION_TEMPLATE_FILENAME
        self.results_filename: str = self.DEFAULT_RESULTS_FILENAME

        self.number_of_applications: int = self.DEFAULT_NUMBER_OF_APPLICATIONS
        self.number_of_devices: int = self.DEFAULT_NUMBER_OF_DEVICES
        self.wifi_range: float = self.DEFAULT_WIFI_RANGE

        self._3D_space: Dict[str,Union[int,float]] = self.DEFAULT_3D_SPACE

        self.app_duration: int = self.DEFAULT_APP_DURATION

    def load_yaml(self, config_file_path: str) -> None:
        """Loads settings from a YAML file.

        Args:
            config_file_path (str): Configuration File Path
        """
        try:
            with open(config_file_path, 'r') as config_file:
                self.parsed_yaml = yaml.safe_load(config_file)
        except FileNotFoundError:
            logging.error("Configuration File Not Found, using default settings.")

    def setup_logging(self) -> None:
        """Initializes logging based on parsed YAML."""

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

        self.log_filename = self.parsed_yaml.get('logfile', 'log.txt')

        logging.basicConfig(filename=self.log_filename, encoding='utf-8', level=self.log_level)
        logging.info('\n')

    def _set_attribute_from_yaml(self, attr_name: str, yaml_path: list, value_type: type) -> None:
        """
        Helper function to set attribute from parsed YAML.

        Args:
            attr_name (str): The name of the attribute to set.
            yaml_path (list): The list of keys to navigate the YAML dictionary.
            value_type (type): The type to cast the value to (e.g., int, float, str).
        """
        try:
            value = self.parsed_yaml
            for key in yaml_path:
                value = value[key]
            setattr(self, attr_name, value_type(value))
        except (KeyError, TypeError) as e:
            logging.error(f"Config Error, Default simulation value {getattr(self, attr_name)} used for entry {e}")

    def set_options(self, options: argparse.Namespace) -> None:
        """Sets other options based on parsed YAML and command-line options."""

        self._set_attribute_from_yaml('devices_template_filename', ['template_files', 'devices'], str)
        self._set_attribute_from_yaml('application_template_filename', ['template_files', 'applications'], str)
        self._set_attribute_from_yaml('number_of_applications', ['application_number'], int)
        self._set_attribute_from_yaml('number_of_devices', ['device_number'], int)
        self._set_attribute_from_yaml('wifi_range', ['wifi_range'], float)

        if options.app_number_override:
            with open(options.app_number_override, 'r') as app_numbers:
                data = yaml.safe_load(app_numbers)
            self.number_of_applications = int(data['application_number'])
            print(f"override detected, stress testing with {self.number_of_applications} applications")

    # Simulated 2D/3D space
        for boundary in self._3D_space.keys():
            self._set_attribute_from_yaml(f'_3D_space["{boundary}"]', ['device_positionning', boundary], float)

        self._set_attribute_from_yaml('app_duration', ['app_duration'], float)

        # Setting options
        try:
            self.results_filename = options.results
        except (KeyError,AttributeError) as e:
            logging.error(f"{e}, processing output will be default {self.results_filename}")

        self.results_filename = getattr(options, 'results', self.results_filename)
        self.devices_file = getattr(options, 'devices', None)
        self.applications_file = getattr(options, 'applications', None)
        self.arrivals_file = getattr(options, 'arrivals', None)
        self.dry_run = getattr(options, 'dry_run', False)
