import yaml
import logging
import datetime
import os
import random
import networkx as nx
import matplotlib.pyplot as plt

from modules.db.interact_db import (create_db, populate_db, dump_from_db)
from modules.ResourceManagement import custom_distance

class Config():
    def __init__(self, options, env) -> None:
        """
        Initializes the application configuration with basic values
        Assigns default values if no values are given

        Args:
            options : parsed arguments
            env : Environment

        Attributes:
            parsed_yaml : dict, contains the outpout from loading the configuration YAML file, stored as a dict
            log_level :
            log_filename :
            database_file :
            number_of_applications :
            number_of_devices : int, number of devices
            wifi_range : float, distance necessary to establish links between two devices, defaults to 6m

        Returns:
            None
        """

        self.parsed_yaml = None
        self.log_level = None
        self.log_filename = None

        config_file_not_found = False

        self.database_file = 'db.sqlite'

        self.number_of_applications = 500
        self.number_of_devices = 40
        self.wifi_range = 6

        self._3D_space = {"x_min" : 0,
                        "x_max" : 40,
                        "y_min" : 0,
                        "y_max" : 40,
                        "z_min" : 0,
                        "z_max" : 0}

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
            self.database_file = self.parsed_yaml['database_url']['device']
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default solution uses 'db.sqlite' in the project's root")

        # Device database renaming
        not_all_checked = True
        while not_all_checked:
            try:
                if options.scratchdevicedb:
                    date_string = datetime.datetime.now().isoformat(timespec='minutes').replace(":","-")
                    os.rename(self.database_file, f"modules/db/archives/{self.database_file}-{date_string}")
                not_all_checked = False
            except KeyError as e:
                logging.error(f"No entry in configuration file for {e}, default solution uses existing database even if 'scratchdevicedb' parameter was given ")
            except FileNotFoundError:
                if not os.path.exists("modules/db/archives/"):
                    logging.error(f"Destination folder does not exist, creating folder, then retrying")
                    os.makedirs("modules/db/archives/")
                else:
                    logging.error(f"'{self.database_file}' not found, no need to rename")
                    not_all_checked = False
            except TypeError:
                logging.error("Configuration File Not Found, default solution is using existing database")

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

        devices = list()

        # Simulated 2D/3D space
        for boundary in self._3D_space.keys():
            try:
                self._3D_space[boundary] = int(self.parsed_yaml['device_positionning'][boundary])
            except (KeyError,TypeError) as e:
                logging.error(f"Default simulation value {self._3D_space[boundary]} used for entry {boundary}")

        try:
            if not os.path.isfile(self.database_file):
                logging.info("Generating random device positions")
                devices = list()
                self.generate_and_plot_devices_positions(devices)
                create_db(self.database_file)
                populate_db(devices, self.database_file)
        except KeyError as e:
            logging.error(f"No entry in configuration file for {e}, default solution uses existing database even if 'scratchdevicedb' parameter was given ")

        logging.info("Generating simulation environment")

        try:
            dump_from_db(env, self.database_file)
        except Exception as e:
            raise e


    def generate_and_plot_devices_positions(self, devices):
        """
        Defines random devices position
        Each device will be represented with its coordinates (x, y, z)

        Args:
        ----
            devices : list, List of coords
        """
        n_devices = self.number_of_devices # Number of devices

        for j in range(n_devices):
            # Processing device position, random x, y, z fixed to between various values (z=0 for now)
            x = round(random.random() * (self._3D_space['x_max'] - self._3D_space['x_min']) + self._3D_space['x_min'],2)
            y = round(random.random() * (self._3D_space['y_max'] - self._3D_space['y_min']) + self._3D_space['y_min'],2)
            z = round(random.random() * (self._3D_space['z_max'] - self._3D_space['z_min']) + self._3D_space['z_min'],2)

            devices.append([x,y,z])


        # We'll try our hand on plotting everything in a graph

        # Creating a graph
        G = nx.Graph()

        # We add the nodes, our devices, to our graph
        for i in range(len(devices)):
            G.add_node(i, pos=devices[i])

        # We add the edges, to our graph, which correspond to wifi reachability

        for i in range(len(devices)):
            for j in range(i+1, len(devices)):
                distance = custom_distance(devices[i][0],devices[i][1],devices[i][2],devices[j][0],devices[j][1],devices[j][2])
                if distance < self.wifi_range:
                    ### We add edges if we have coverage
                    G.add_edge(i, j)

        # Let's try plotting the network

        # We alread have the coords, but let's process it again just to be sure
        x_coords, y_coords, z_coords = zip(*devices)

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
        plt.savefig("fig/graph.png")
