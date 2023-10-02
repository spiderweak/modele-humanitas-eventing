from typing import Optional, Dict, Any, Union, List
import random

class Processus:

    next_id: int = 0
    DEFAULT_RESOURCES: Dict[str, Union[int, float]] = {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}
    RANDOMIZER_DEFAULT_RESOURCE: Dict[str, Dict[str, Any]] = {
        'cpu': {'choices': [0.5, 1, 2, 3, 4]},
        'gpu': {'choices': [0, 0, 0, 0, 0.5, 1, 2, 4]},
        'mem': {'range': (0.025, 1), 'factor': 4 * 1024},
        'disk': {'range': (1, 10), 'factor': 10 * 1024},
    }

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

        if data:
            self.id = data.get("proc_id", Processus._generate_id())
            self.app_id = data.get("app_id", -1)
            self.resource_request = data.get("proc_resource_request", self.DEFAULT_RESOURCES.copy())
            self.resource_allocation = data.get("proc_resource_allocation", {key: 0 for key in self.resource_request})
        else:
            self.id = Processus._generate_id()
            self.app_id = -1
            self.resource_request = self.DEFAULT_RESOURCES.copy()
            self.resource_allocation = self.DEFAULT_RESOURCES.copy()


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
        """Return the Processus signature as a json string to be parsed by a json exporter

        Returns:
            dict
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
        """Get the application ID associated with this processus.

        Returns:
            int: The application ID.
        """
        return self._app_id

    @app_id.setter
    def app_id(self, app_id: int) -> None:
        """Set the application ID for this processus.

        Args:
            app_id (int): The new application ID.
        """
        self._app_id = app_id


    @property
    def resource_request(self) -> Dict[str, Union[int, float]]:
        """
        Get the resource request dictionary for this processus.

        Returns:
            Dict[str, Union[int, float]]: The resource request dictionary.
        """
        return self._resource_request

    @resource_request.setter
    def resource_request(self, new_resource_request: Dict[str, Union[int, float]]) -> None:
        """Set the resource request dictionary for this processus.

        Args:
            new_resource_request (Dict[str, Union[int, float]]): The new resource request dictionary.
        """
        if not hasattr(self, '_resource_request'):
            self._resource_request: Dict[str, Union[int, float]] = {}

        for resource, resource_requested in new_resource_request.items():
            self.setProcessusResourceRequest(resource, resource_requested)

    def setProcessusResourceRequest(self, resource: str, resource_requested: Union[int, float]):
        """Set Processus Resource (CPU, GPU, Mem, Disk) Request

        Args:
            resource (str`): Resource name
            resource_requested (float): Quantity of a given resource to request from device.
        """
        if not hasattr(self, '_resource_request'):
            self._resource_request: Dict[str, Union[int, float]] = {}
        self._resource_request[resource] = resource_requested


    def randomProcInit(self):
        """Randomly initialize the resource request for this processus:
            Random number of CPU between 0.5 and 4
            Random number of GPU between 0 and 8
            Random Memory between 0.1 and 4 GigaBytes
            Random Disk space between 10 and 100 GigaBytes
        """
        random_resource_request: Dict[str, Union[int, float]] = {}

        for resource_type in self.resource_request.keys():
            random_resource_request[resource_type] = self._get_random_value(resource_type)

        self.resource_request = random_resource_request


    def _get_random_value(self, resource_type: str) -> Union[int, float]:
            """Helper method to get a random value for a given resource type."""
            # Randomizer for 'choices' type values (CPU/GPU)
            choices = self.RANDOMIZER_DEFAULT_RESOURCE[resource_type].get('choices')
            if choices:
                return random.choice(choices)

            # Randomizer for 'range' type values (Mem/Disk)
            value_range = self.RANDOMIZER_DEFAULT_RESOURCE[resource_type].get('range')
            factor = self.RANDOMIZER_DEFAULT_RESOURCE[resource_type].get('factor', 1)
            if value_range:
                min_val, max_val = value_range
                return (random.random() * (max_val - min_val) + min_val) * factor

            return 0  # Default to 0 if no range or choices are defined

