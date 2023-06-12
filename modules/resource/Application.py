"""
Application module, defines the Application Class

Usage:

"""
import numpy as np
import random

from modules.resource.Processus import Processus

# Number of group of 10 ms
TIME_PERIOD = 24 * 60 * 60 * 100

class Application:
    """
    An application is defined as a graph of processus
    (array of array, for now, might be a networkx graph)
    Initialized to empty data

    Attributes:
    ----------
    id: `int`
        Application ID
    duration: `int`
        Application duration in tens of milliseconds
    processus_list: list of `Processus`
        List of `Processus` application members
    proc_links: matrix of `int`
        Integer value corresponding to bandwidth request over virtual links
    deployment_info: dict of `Processus`:`int`
        Dictionary linking `Processus` and `Device` IDs
    """

    id = 0


    @classmethod
    def _generate_id(cls):
        """
        Class method for id generation
        Assigns id then increment for next generation

        Returns:
        -------
        result: `int`
            Application ID
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
        ----
        num_procs : `int`
            default 1, number of processus in the application

        Attributes:
        ----------
        id : `int`
            Application identifier
        duration : `int`
            Application duration (in chuncks of 10ms)
        num_procs : `int`
            Number of processus in application
        processus_list : <List>`Processus`
            List of processus part of the application
        proc_links : <Matrix>`int`
            Bandwidth between application components
        deployment_info : `dict`
            Matching between Processus ID and Device ID
        """

        self.id = Application._generate_id()

        # Application duration
        self.duration = 0

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


    def setAppID(self, id):
        """
        Used to set an application's ID by hand if necessary

        Args:
        ----
            id : int, new application ID
        """

        self.id=id


    # Random application initialization
    def randomAppInit(self, num_procs=3, num_proc_random=True):
        """
        Random initialization of the application

        Args:
        ----
            num_procs : int, number of processus to consider
            num_proc_random : Bool, default to True for random number of processus deployed between 1 and num_proc
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

        # Random value between 15 and 60 minutes
        self.setAppDuration(random.randint(TIME_PERIOD/96, TIME_PERIOD/24))


    def setAppDuration(self, duration = TIME_PERIOD/48):
        """
        Application execution duration in milliseconds

        Default value is 30 minutes

        Args:
        ----
        duration: `int`
            Application duration in tens of milliseconds
        """

        self.duration = duration


    def app_yaml_parser(self, app_yaml):
        """
        Parser to load application characteristics from yaml file.

        Args:
        ----
        app_yaml : `dict`
            dictionary from yaml file content parsing
        """

        application_content = app_yaml["Application"]

        self.num_procs = len(application_content)
        self.processus_list = list()

        for yaml_processus in application_content:
            new_processus = Processus()
            new_processus.processus_yaml_parser(yaml_processus)
            new_processus.app_id = self.id
            self.processus_list.append(new_processus)

        links_details = app_yaml["AppLinks"]

        self.proc_links = np.zeros((self.num_procs, self.num_procs))

        for app_links in links_details:
            link = app_links['Link']
            self.proc_links[link['Processus 1']][link['Processus 2']] = int(link['Bandwidth'])


    def setDeploymentInfo(self, deployed_onto_device):
        """
        Creates a dictionary matching `Processus` and `Device` ID

        Args:
        ----
        deployed_onto_device : list of `int`
            List of devices IDs that reference processus hosts
        """

        for i in range(len(deployed_onto_device)):
            self.deployment_info[self.processus_list[i]] = deployed_onto_device[i]
