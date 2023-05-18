"""
Application module, defines the Application Class

Usage:

"""
import numpy as np
import random

from modules.Processus import Processus

TIME_PERIOD = 24*60*60*100

class Application:

    id = 0


    @classmethod
    def _generate_id(cls):
        """
        Class method for id generation
        Assigns id then increment for next generation

        Args:
            None

        Returns:
            result : int, Application ID
        """
        result = cls.id
        cls.id +=1
        return result


    def __init__(self, num_procs = 1) -> None:
        """
        An application is defined as a graph of processus
        (array of array, for now, might be a networkx graph)
        Initializes to empty data

        Args:
            num_procs : int, default 1, number of processus in the application

        Returns:
            None
        """

        self.id = Application._generate_id()
        # Initializes the number of processus required by the application
        self.num_procs = num_procs

        # Initializes the list of processus
        self.processus_list = list()
        for _ in range(num_procs):
            # Generate a new (non-initialized) processus
            new_processus = Processus()
            # Adds the new processus to the list
            self.processus_list.append(new_processus)

        # Initializes the processus links matrix to 0
        self.proc_links = np.zeros((num_procs, num_procs))

        self.deployment_info = dict()

        self.duration = 0


    def setAppID(self, id):
        """
        Used to set an application's ID by hand if necessary

        Args:
            id : int, new application ID

        Returns:
            None
        """
        self.id=id


    # Random application initialization
    def randomAppInit(self, num_procs=3, num_proc_random=True):
        """
        Random initialization of the application

        Args:
            num_procs : int, number of processus to consider
            num_proc_random : Bool, default to True for random number of processus deployed between 1 and num_proc

        Returns:
            None
        """
        # If numproc is set to random, randomize the number of processus deployed
        if num_proc_random:
            num_procs = random.randint(1,num_procs)

        # Set the num_procs value
        self.num_procs = num_procs

        # Initialize a random list of processus, starts with empty list
        self.processus_list = list()
        for _ in range(num_procs):
            # New processus generation
            new_processus = Processus()
            # Processus initialized to random values from Processus class
            new_processus.randomProcInit()
            # Adds processus to list
            self.processus_list.append(new_processus)

        # Generates the random link matrix between processus
        # Links will be symetrical, link matrix initialized to zero
        proc_links = np.zeros((num_procs, num_procs))
        for i in range(num_procs):
            for j in range(i+1, num_procs):
                # Generate a random link with between processus i and processus j, j>i
                if j == i+1:
                    # We garanty a chain between processus i and i+1
                    proc_links[i][j] = 1
                else:
                    # Else, we might have a link, but not garanteed
                    proc_links[i][j] = random.choice([0,1])

                # Random generated value is either 0 or a random value corresponding to 10 to 50 MBytes
                proc_links[i][j] = proc_links[i][j] * random.choice([10,20,30,40,50]) * 1024
                proc_links[j][i] = proc_links[i][j]

        # Sets the generated value as part of the device creation
        self.proc_links = proc_links

        self.duration = random.randint(TIME_PERIOD/96,TIME_PERIOD/24)


    def app_yaml_parser(self, app_yaml):
        """
        Parser to load application characteristics from yaml file.

        Args:
            app_yaml : dictionary from yaml file content

        Returns:
            None
        """
        application_content = app_yaml["Application"]

        self.num_procs = len(application_content)
        self.processus_list = list()

        for yaml_processus in application_content:
            new_processus = Processus()
            new_processus.processus_yaml_parser(yaml_processus)
            self.processus_list.append(new_processus)

        links_details = app_yaml["AppLinks"]

        self.proc_links = np.zeros((self.num_procs, self.num_procs))

        for app_links in links_details:
            link = app_links['Link']
            self.proc_links[link['Processus 1']][link['Processus 2']] = int(link['Bandwidth'])

        self.duration = random.randint(TIME_PERIOD/96,TIME_PERIOD/24) # Random for now


    def setDeploymentInfo(self, deployed_onto_device):

        for i in range(len(deployed_onto_device)):
            self.deployment_info[self.processus_list[i]] = deployed_onto_device[i]


