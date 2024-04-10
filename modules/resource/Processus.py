from typing import Optional, Dict, Any, Union, List
import random

class Processus:
    """
    The Processus class represents a sub-component of an Application and is responsible for managing
    its resource requirements and allocations.

    This class provides methods for comparing Processus instances, combining their resource requirements,
    and generating JSON representations.

    Comparison is based on an arbitrary resource priority order.

    Attributes:
        id (int): Unique identifier for the Processus instance.
        app_id (int): Identifier for the application to which this Processus instance belongs.
        resource_request (Dict[str, Union[int, float]]): Dictionary representing the resource requirements for this Processus.
        resource_allocation (Dict[str, Union[int, float]]): Dictionary representing the allocated resources for this Processus.
    """

    next_id: int = 0
    DEFAULT_RESOURCES: Dict[str, Union[int, float]] = {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}
    RANDOMIZER_DEFAULT_RESOURCE: Dict[str, Dict[str, Any]] = {
        'cpu': {'choices': [0.5, 1, 2, 3, 4]},
        'gpu': {'choices': [0, 0, 0, 0, 0.5, 1, 2, 4]},
        'mem': {'range': (0.0125, 1), 'factor': 8 * 1024},
        'disk': {'range': (1, 10), 'factor': 100 * 1024},
    }

    # Arbitrary resource order
    # To compare Processus, we chose to decide on an arbitrary resource order,
    # Comparing two Processus object first mean comparing there GPU request, then CPU, then memory and finally disk size
    RESOURCE_ORDER = ['gpu', 'cpu', 'mem', 'disk']


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


    def __init__(self, data: Optional[Dict[str, Any]] = None, * , priority: int = 0) -> None:
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
            self.resource_allocation: Dict[str, Union[int, float]] = data.get("proc_resource_allocation", {key: 0 for key in self.resource_request})
        else:
            self.id = Processus._generate_id()
            self.app_id = -1
            self.resource_request = self.DEFAULT_RESOURCES.copy()
            self.resource_allocation = self.DEFAULT_RESOURCES.copy()

        self.priority = priority


    def __add__(self, other : "Processus") -> "Processus":
        if isinstance(other, int):
            return self

        if isinstance(other, Processus):

            all_keys = set(self.resource_request.keys()) | set(other.resource_request.keys())
            combined_resource_request = {
                key: self.resource_request.get(key, 0) + other.resource_request.get(key, 0)
                for key in all_keys
            }

            app_id = self.app_id if self.app_id == other.app_id else -1

            new_proc_data = {
                "app_id" : app_id,
                "proc_resource_request": combined_resource_request
            }

            new_proc = Processus(new_proc_data)

            return new_proc

        else:
            raise TypeError("Unsupported operand type for +: 'Processus' and '{}'".format(type(other).__name__))

    def __radd__(self, other : "Processus")-> "Processus":
        return self + other


    def __lt__(self, other : "Processus") -> bool:
        """Compare two Processus objects based on their resource requests.

        The comparison uses an arbitrary order of resources: `RESOURCE_ORDER`.

        Parameters:
            other : Processus
                The other Processus object to compare with.

        Returns:
            bool
                True if the current object is "less than" the other, based on resource requests.
                False otherwise.

        Raises:
            TypeError
                If the other object is not a Processus instance.
        """
        if isinstance(other, Processus):
            for resource in self.RESOURCE_ORDER:
                # We consider values set to zero in case the resources does not exist
                self_val = self.resource_request.get(resource, 0)
                other_val = other.resource_request.get(resource, 0)
                if self_val > other_val:
                    return False
            return True
        else:
            raise TypeError(f"Cannot compare Processus with {type(other).__name__}")

    def __gt__(self, other : "Processus") -> bool:
        return other < self


    def __json__(self) -> Dict:
        """Returns a dictionary containing the Processus' attributes.

        Returns:
            dict: A dictionary containing the 'proc_id' and 'proc_resource_request'.
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
            self.set_processus_resource_request(resource, resource_requested)

    def set_processus_resource_request(self, resource: str, resource_requested: Union[int, float]):
        """Set Processus Resource (CPU, GPU, Mem, Disk) Request

        Args:
            resource (str`): Resource name
            resource_requested (float): Quantity of a given resource to request from device.
        """
        if not hasattr(self, '_resource_request'):
            self._resource_request: Dict[str, Union[int, float]] = {}
        self._resource_request[resource] = resource_requested


    @property
    def priority(self) -> int:
        """
        Get the priority level of the object.

        Returns:
            Priority level as an integer.
        """
        return self._priority

    @priority.setter
    def priority(self, priority_level: int):
        """
        Set the priority level of the object.

        Args:
            priority_level(int): New priority level to set.
        """
        self._priority = priority_level


    def random_proc_init(self):
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

