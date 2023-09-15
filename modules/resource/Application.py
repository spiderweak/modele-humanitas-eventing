"""
Application module, defines the Application Class

usage:
    from Application import Application
    app = Application()

"""
import numpy as np
import random
from typing import List, Dict, Union

from modules.resource.Processus import Processus

# Number of group of 10 ms
TIME_PERIOD = 8640000 #24 * 60 * 60 * 100

class Application:
    """
    An application is defined as a graph of processus (array of arrays, potentially a networkx graph in the future).

    It is initialized with empty data by default, usually populated with  a list of processus, a matrix of processus links, and device deployment information.

    Attributes:
    -----------
    id : int
        The ID of the application, generated automatically during initialization.
    duration : int
        The duration of the application in chunks of 10 ms.
    num_procs : int
        The number of processus in the application.
    processus_list : List[Processus]
        A list of Processus objects representing the individual processus in the application.
    proc_links : np.ndarray
        A matrix representing the bandwidth request over virtual links between processus.
    deployment_info : dict
        A dictionary linking Processus objects to Device IDs.
    """

    next_id = 0


    @classmethod
    def _generate_id(cls):
        """
        Class method for ID generation.
        Generates a unique ID for a new Application object.
        Assigns ID then increments for next generation.

        Returns:
        --------
        result : int
            Application ID
        """

        result = cls.next_id
        cls.next_id +=1
        return result


    def __init__(self, data: Union[Dict, None] = None, num_procs: int = 1) -> None:
        """
        Initializes a new Application object with the given data dictionary and number of processus.

        Args:
        -----
        data : dict, optional
            A dictionary containing initial data for the application.
            If provided, the application will be initialized with the values from this dictionary.
            Defaults to None.
        num_procs : int, optional
            The number of processus in the application.
            Defaults to 1.
        """

        self.id: int = Application._generate_id()

        # Application duration
        self.duration: int = 0

        # Initializes the number of processus required by the application
        self.num_procs: int = num_procs

        # Initializes the list of processus
        self.processus_list: List[Processus] = []

        # Initializes the processus links matrix to 0
        self.proc_links: np.ndarray = np.zeros((num_procs, num_procs))

        self.deployment_info: Dict[Processus, int] = {}

        if data:
            self.initFromDict(data)
        else:
            for _ in range(num_procs):
                # Generate a new (non-initialized) processus
                new_processus = Processus()
                # Adds the new processus to the list
                self.processus_list.append(new_processus)


    def __json__(self) -> Dict:
        """
        Returns the Application signature as a JSON serializable dictionary
        to be parsed by a JSON exporter.

        Returns:
        --------
        dict
            A dictionary representing the Application object.
        """

        # Ensuring all values in the proc_links are integers for JSON serialization
        proc_links = [[int(val) for val in row] for row in self.proc_links]

        # Using the __json__ method of the Processus class to serialize each Processus object in processus_list
        proc_list_serialized = [proc.__json__() for proc in self.processus_list]


        return {
            "app_id" : self.id,
            "duration" : self.duration,
            "proc_list" : proc_list_serialized,
            "proc_links" : proc_links
        }


    def setAppID(self, id: int) -> None:
        """
        Used to set an application's ID by hand if necessary

        Args:
        -----
        id : int
            New application ID
        """

        self.id = id

    def randomAppInit(self, num_procs: int = 3, num_proc_random: bool = True) -> None:
        """
        Random initialization of the application.

        Parameters
        ----------
        num_procs : int, optional
            Number of processus to consider, by default 3
        num_proc_random : bool, optional
            If True, the number of processus deployed is randomly chosen between 1 and num_procs, by default True
        """

        # If num_proc_random is set to true, randomize the number of processus deployed
        if num_proc_random:
            num_procs = random.randint(1, num_procs)

        # Set the num_procs value
        self.num_procs = num_procs

        # Initialize a random list of processus, starts with an empty list
        self.processus_list = [Processus() for _ in range(num_procs)]
        for proc in self.processus_list:
            proc.randomProcInit()

        # Generates the random link matrix between processus
        # Links will be symmetrical, link matrix initialized to zero
        proc_links = np.zeros((num_procs, num_procs))
        for i in range(num_procs):
            for j in range(i+1, num_procs):
                # Generate a random link with between processus i and processus j, j>i
                link_value = random.choice([0,1]) if j != i+1 else 1
                link_value *= random.choice([10,20,30,40,50]) * 1024
                proc_links[i][j] = proc_links[j][i] = link_value

        # Sets the generated value as part of the device creation
        self.proc_links = proc_links

        # Random value between 15 and 60 minutes
        self.setAppDuration(random.randint(int(TIME_PERIOD/96), int(TIME_PERIOD/24)))


    def setAppDuration(self, duration: int = int(TIME_PERIOD/48)) -> None:
        """
        Sets the application execution duration.

        The default value corresponds to a duration of 30 minutes.

        Parameters
        ----------
        duration : int
            Application duration in milliseconds, by default 1800000 (30 minutes)
        """

        self.duration = duration


    def app_yaml_parser(self, app_yaml: Dict) -> None:
        """
        Parser to load application characteristics from a YAML file.

        Args:
        -----
        app_yaml : dict
            Dictionary derived from YAML file content parsing
        """

        try:
            application_content = app_yaml["Application"]
        except KeyError:
            raise KeyError("The 'Application' key was not found in the YAML file.")

        self.num_procs = len(application_content)
        self.processus_list = []

        for yaml_processus in application_content:
            new_processus = Processus()
            new_processus.processus_yaml_parser(yaml_processus)
            new_processus.app_id = self.id
            self.processus_list.append(new_processus)

        try:
            links_details = app_yaml["AppLinks"]
        except KeyError:
            raise KeyError("The 'AppLinks' key was not found in the YAML file.")

        self.proc_links = np.zeros((self.num_procs, self.num_procs))

        for app_links in links_details:
            try:
                link = app_links['Link']
                p1, p2, bandwidth = link['Processus 1'], link['Processus 2'], int(link['Bandwidth'])
            except KeyError as e:
                raise KeyError(f"A necessary key was not found in the 'AppLinks' section: {e}")

            self.proc_links[p1][p2] = bandwidth
            self.proc_links[p2][p1] = bandwidth  # Assuming the bandwidth is the same in both directions


    def setDeploymentInfo(self, deployed_onto_device: List[int]) -> None:
        """
        Creates a dictionary matching `Processus` and `Device` ID.

        Args:
        -----
        deployed_onto_device : List[int]
            List of device IDs that reference processus hosts.

        Raises:
        -------
        ValueError:
            If the length of deployed_onto_device does not match the number of processus in the application.
        """

        if len(deployed_onto_device) != len(self.processus_list):
            raise ValueError("The length of deployed_onto_device does not match the number of processus.")

        for i, device_id in enumerate(deployed_onto_device):
            self.deployment_info[self.processus_list[i]] = device_id


    def getAppProcsIDs(self) -> List[int]:
        """
        Retrieves the IDs of all processus in the application.

        Returns:
        --------
        List[int]
            A list containing the IDs of all processus in the application.
        """

        return [proc.getProcessusID() for proc in self.processus_list]


    def getAppProcByID(self, id: int) -> Processus:
        """
        Retrieves a processus by its ID.

        Args:
        -----
        id : int
            The ID of the processus to retrieve.

        Returns:
        --------
        Processus
            The processus with the specified ID.

        Raises:
        -------
        KeyError
            If no processus with the specified ID is found.
        """

        try:
            return next(proc for proc in self.processus_list if proc.getProcessusID() == id)
        except StopIteration:
            raise KeyError(f"Processus with ID {id} not found.")


    def initFromDict(self, data: Dict) -> None:
        """
        Initializes the Application object from a dictionary of data.

        Args:
        -----
        data : Dict
            Dictionary containing data to initialize the Application object with. Should contain keys:
            - 'app_id': (int) The ID for the application.
            - 'duration': (int) The duration for the application.
            - 'proc_list': (List[Dict]) List of dictionaries representing processus objects.
            - 'proc_links': (List[List[int]]) Matrix representing the processus links.

        Returns:
        --------
        None
        """

        self.setAppID(data['app_id'])

        self.setAppDuration(data['duration'])

        for proc in data.get("proc_list", []):
            self.processus_list.append(Processus(data=proc))

        self.proc_links = np.array(data.get("proc_links", []))
