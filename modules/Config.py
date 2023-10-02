import yaml
import logging
import datetime
import os
import networkx as nx
import matplotlib.pyplot as plt

from modules.ResourceManagement import custom_distance

import json
class Config():
    def __init__(self, options, env) -> None:
        """
        Initializes the application configuration with basic values
        Assigns default values if no values are given

        Args:
        -----
        options : `argparse.Namespace`
            parsed arguments from argument parser (`argparse`) module
        env : `Environment`
            Simulation environment

        Attributes:
        -----------
        parsed_yaml : `dict`
            Contains the outpout from loading the configuration YAML file, stored as a dict
        log_level : `int`
            Integer representation of the parsed log level
        log_filename : `str`
            LogFile name
        devices_template_filename : `str`
            Device Template Filename
        application_template_filename : `str`
            Application Template Filename
        number_of_applications : `int`
            Number of application to test
        number_of_devices : `int`
            Number of devices in the infrastructure
        wifi_range : `float`
            Distance necessary to establish links between two devices, defaults to 6m
        """

        self.parsed_yaml = None
        self.log_level = None
        self.log_filename = None

        config_file_not_found = False

        self.devices_template_filename = "devices.json"
        self.application_template_filename = "application.json"
        self.results_filename = "results.json"

        self.number_of_applications = 500
        self.number_of_devices = 40
        self.wifi_range = 6

        self._3D_space = {"x_min" : 0,
                        "x_max" : 40,
                        "y_min" : 0,
                        "y_max" : 40,
                        "z_min" : 0,
                        "z_max" : 0}

        self.app_duration = 0

        # Parsing the folder
        try:
            with open(options.config, 'r') as config_file:
                self.parsed_yaml = yaml.safe_load(config_file)
        except FileNotFoundError:
            self.parsed_yaml = None
            config_file_not_found = True

        # Log level
        try:
            match self.parsed_yaml['loglevel']:
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

        # Log file
        try:
            self.log_filename = self.parsed_yaml['logfile']
        except (KeyError, TypeError):
            self.log_filename = 'log.txt'

        logging.basicConfig(filename=self.log_filename, encoding='utf-8', level=self.log_level)
        logging.info('\n')
        if config_file_not_found:
            logging.error("Configuration File Not Found, defaulting to default configuration")
            logging.error("\n")

        # Template files
        try:
            self.devices_template_filename = self.parsed_yaml['template_files']['devices']
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default solution uses 'devices.json' in the project's root")

        try:
            self.application_template_filename = self.parsed_yaml['template_files']['applications']
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default solution uses 'applications.json' in the project's root")

        # Number of simulated applications to deploy
        try:
            self.number_of_applications = int(self.parsed_yaml['application_number'])
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default simulation value is 500 applications")
        except TypeError:
            logging.error("Configuration File Not Found, default simulation value is 500 applications")

        # Number of simulated devices
        try:
            self.number_of_devices = int(self.parsed_yaml['device_number'])
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default simulation value is 40 devices")
        except TypeError:
            logging.error("Configuration File Not Found, default simulation value is 40 devices")

        # Simulated wifi range for device connectivity
        try:
            self.wifi_range = int(self.parsed_yaml['wifi_range'])
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default simulation value is 6 meters")
        except TypeError:
            logging.error("Configuration File Not Found, default simulations is 6 meters")

        # Simulated 2D/3D space
        for boundary in self._3D_space.keys():
            try:
                self._3D_space[boundary] = int(self.parsed_yaml['device_positionning'][boundary])
            except (KeyError,TypeError) as e:
                logging.error(f"Default simulation value {self._3D_space[boundary]} used for entry {boundary}")

        # Setting application durations
        try:
            self.app_duration = int(self.parsed_yaml['app_duration'])
        except (KeyError,TypeError) as e:
            logging.error(f"Default simulation value {self.app_duration} used for entry {e}")

        try:
            self.results_filename = options.results
        except (KeyError,AttributeError) as e:
            logging.error(f"{e}, processing output will be default {self.results_filename}")

        try:
            self.devices_file = options.devices
            self.applications_file = options.applications
            self.arrivals_file = options.arrivals
        except AttributeError:
            pass

        try:
            self.dry_run = options.dry_run
        except (KeyError, AttributeError):
            self.dry_run = False
