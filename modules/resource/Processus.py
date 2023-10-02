import random

from typing import Optional, Dict, Any, Union

class Processus:

    next_id: int = 0
    DEFAULT_RESOURCES: Dict[str, Union[int, float]] = {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}


    @classmethod
    def _generate_id(cls) -> int:
        """Class method for id generation
        Assigns id then increment for next generation

        Returns:
            result (int): Processus ID
        """
        result = cls.next_id
        cls.next_id +=1
        return result


    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        """A processus is a sub-part of an application
        A processus is defined as a values corresponding to resource requests
        Initializes the Processus object.

        Args:
            data (Optional[Dict[str, Any]], optional): A dictionary to initialize the object's attributes. Defaults to None.
        """

        self.id = Processus._generate_id()
        self.app_id = -1

        self.resource_request = self.DEFAULT_RESOURCES.copy()
        self.resource_allocation = self.DEFAULT_RESOURCES.copy()

        if data:
            self.id = data.get("proc_id", self.id)
            self.app_id = data.get("app_id", self.app_id)

            self.resource_request = data.get("proc_resource_request", self.DEFAULT_RESOURCES.copy())
            self.resource_allocation = data.get("proc_resource_allocation", {key: 0 for key in self.resource_request})


    def __add__(self, other):

        if isinstance(other, int):
            if other == 0:
                return self

        if isinstance(other, Processus):
            new_proc = Processus()

            new_proc.setProcessusResourceRequest('cpu', self.resource_request['cpu'] + other.resource_request['cpu'])
            new_proc.setProcessusResourceRequest('gpu', self.resource_request['gpu'] + other.resource_request['gpu'])
            new_proc.setProcessusResourceRequest('mem', self.resource_request['mem'] + other.resource_request['mem'])
            new_proc.setProcessusResourceRequest('disk', self.resource_request['disk'] + other.resource_request['disk'])

            return new_proc
        else:
            raise TypeError


    def __radd__(self, other):
        return self.__add__(other)


    def __lt__(self, other):
        # Arbitrary resource order
        resource_order = ['gpu', 'cpu', 'mem', 'disk']

        for resource in resource_order:
            if self.resource_request[resource] > other.resource_request[resource]:
                return False
        return True


    def __gt__(self, other):
        return other.__lt__(self)


    def __json__(self):
        """
        Returns the Processus signature as a json string to be parsed by a json exporter

        Returns:
        --------
            `dict`
        """

        return {
            "proc_id" : self.id,
            "proc_resource_request" : self.resource_request
        }


    @property
    def id(self) -> int:
        """Used to get a processus's ID

        Returns:
            id (int): Processus ID
        """
        return self._id

    @id.setter
    def id(self, id: int):
        """Used to set a processus's ID by hand if necessary.
        Note: IDs are usually immutable; use this cautiously.

        Args:
        id (int): New processus ID
        """
        self._id = id

    @property
    def app_id(self) -> int:
        """Gets the application ID associated with this processus.

        Returns:
            int: The application ID.
        """
        return self._app_id

    @app_id.setter
    def app_id(self, app_id: int) -> None:
        """Sets the application ID for this processus.

        Args:
            app_id (int): The new application ID.
        """
        self._app_id = app_id


    @property
    def resource_request(self) -> Dict[str, Union[int, float]]:
        """
        Gets the resource request dictionary for this processus.

        Returns:
            Dict[str, Union[int, float]]: The resource request dictionary.
        """
        return self._resource_request

    @resource_request.setter
    def resource_request(self, new_resource_request: Dict[str, Union[int, float]]) -> None:
        """Sets the resource request dictionary for this processus.

        Args:
            new_resource_request (Dict[str, Union[int, float]]): The new resource request dictionary.
        """
        if not hasattr(self, '_resource_request'):
            self._resource_request: Dict[str, Union[int, float]] = {}

        for resource, resource_requested in new_resource_request.items():
            self.setProcessusResourceRequest(resource, resource_requested)

    def setProcessusResourceRequest(self, resource: str, resource_requested: Union[int, float]):
        """Sets Processus Resource (CPU, GPU, Mem, Disk) Request

        Args:
            resource (str`): Resource name
            resource_requested (float): Quantity of a given resource to request from device.
        """
        if not hasattr(self, '_resource_request'):
            self._resource_request: Dict[str, Union[int, float]] = {}
        self._resource_request[resource] = resource_requested


    def randomProcInit(self):
        """
        Random processus initialization :
            Random number of CPU between 0.5 and 4
            Random number of GPU between 0 and 8
            Random Memory between 0.1 and 4 GigaBytes
            Random Disk space between 10 and 100 GigaBytes

        Args:
        -----
        None

        Returns:
        --------
        None
        """

        self.setProcessusResourceRequest('cpu', random.choice([0.5,1,2,3,4]))
        self.setProcessusResourceRequest('gpu', random.choice([0]*4+[0.5,1,2,4]))
        self.setProcessusResourceRequest('mem', (random.random() * 0.975 + 0.025) * 4 * 1024)
        self.setProcessusResourceRequest('disk', (random.random() * 9 + 1) * 10 * 1024)


    def processus_yaml_parser(self, processus_yaml):
        """
        Parser to load application characteristics from yaml file, usually called from the app configuration.

        Args:
        -----
        processus_yaml : `dict`
            dictionary from yaml file content.

        Returns:
        --------
        None
        """
        processus_content = processus_yaml['Processus']

        self.setProcessusResourceRequest('cpu', processus_content['cpu'])
        self.setProcessusResourceRequest('gpu', processus_content['gpu'])
        self.setProcessusResourceRequest('mem', processus_content['memory'])
        self.setProcessusResourceRequest('disk', processus_content['disk'])

