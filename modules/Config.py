import yaml
import logging
import datetime
import os
import random
import networkx as nx
import matplotlib.pyplot as plt

from modules.Database import Database
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
        database_file : `Database`
            Custom SQLite database object for reading and archival
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

        database_filename = 'db.sqlite'
        self.devices_template_filename = "devices.json"
        self.application_template_filename = "application.json"

        self.database_file = Database(database_filename)

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

        # Device database information
        try:
            database_filename = self.parsed_yaml['database_url']['device']
            self.database_file = Database(database_filename)
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default solution uses 'db.sqlite' in the project's root")

        # Device database renaming
        not_all_checked = True
        while not_all_checked:
            try:
                if options.scratchdevicedb:
                    date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":","-")
                    os.rename(database_filename, f"modules/db/archives/{database_filename}-{date_string}")
                not_all_checked = False
            except KeyError as e:
                logging.error(f"No entry in configuration file for {e}, default solution uses existing database even if 'scratchdevicedb' parameter was given ")
            except FileNotFoundError:
                if not os.path.exists("modules/db/archives/"):
                    logging.error(f"Destination folder does not exist, creating folder, then retrying")
                    os.makedirs("modules/db/archives/")
                else:
                    logging.error(f"'{database_filename}' not found, no need to rename")
                    not_all_checked = False
            except TypeError:
                logging.error("Configuration File Not Found, default solution is using existing database")
            except AttributeError:
                not_all_checked = False

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

        # Database interation
        try:
            if not os.path.isfile(database_filename):
                logging.info("Generating random device positions")
                devices = dict()
                self.generate_and_plot_devices_positions(devices)
                self.database_file.create_db()
                self.database_file.populate_db(devices, self.devices_template_filename)
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default solution uses existing database even if 'scratchdevicedb' parameter was given ")

        logging.info("Generating simulation environment")

        try:
            self.database_file.dump_from_db(env)
        except Exception as e:
            raise e


    def generate_and_plot_devices_positions(self, devices):
        """
        Defines random devices position
        Each device will be represented with its coordinates (x, y, z)

        Args:
        -----
        devices : `dict`
            Coords dictionary
        """

        n_devices = self.number_of_devices # Number of devices

        try:
            with open(self.devices_template_filename) as devices_template_file:
                devices_data = json.load(devices_template_file)
                for device in devices_data:
                    devices[device['id']] = [device['x'],device['y'],device['z']]
        except FileNotFoundError:
            for dev_id in range(n_devices):
            # Processing device position, random x, y, z fixed to between various values (z=0 for now)
                x = round(random.random() * (self._3D_space['x_max'] - self._3D_space['x_min']) + self._3D_space['x_min'],2)
                y = round(random.random() * (self._3D_space['y_max'] - self._3D_space['y_min']) + self._3D_space['y_min'],2)
                z = round(random.random() * (self._3D_space['z_max'] - self._3D_space['z_min']) + self._3D_space['z_min'],2)

                devices[dev_id] = [x,y,z]



        # We'll try our hand on plotting everything in a graph

        # Creating a graph
        G = nx.Graph()

        # We add the nodes, our devices, to our graph
        for dev_id in devices.keys():
            G.add_node(dev_id, pos=devices[dev_id])

        # We add the edges, to our graph, which correspond to wifi reachability

        for dev_id in devices.keys():
            for other_dev_id in devices.keys():
                if dev_id < other_dev_id:
                    distance = custom_distance(devices[dev_id],devices[other_dev_id])
                    if distance < self.wifi_range:
                        ### We add edges if we have coverage
                        G.add_edge(dev_id, other_dev_id)

        # Let's try plotting the network

        # We alread have the coords, but let's process it again just to be sure
        x_coords, y_coords, z_coords = zip(*devices.values())

        #  We create a 3D scatter plot again
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(projection = '3d')

        # Lets trace the graph by hand
        ## Placing the nodes
        ax.scatter(x_coords, y_coords, z_coords, c='b')
        ## Placing the edges by hand
        for i, j in G.edges():
            ax.plot([devices[i][0], devices[j][0]],
                    [devices[i][1], devices[j][1]],
                    [devices[i][2], devices[j][2]], c='lightgray')

        # Set the labels
        ax.set_xlabel('X')
        ax.set_ylabel('Y')

        # Title
        ax.set_title(f'Undirected Graph of Devices with Edge Distance < {self.wifi_range}')

        # Saves the graph in a file
        try:
            os.makedirs("fig") # Will need to rework that, but creates a fig folder to host figures
        except FileExistsError:
            pass
        plt.savefig("fig/graph.png")
