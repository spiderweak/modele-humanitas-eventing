import random

class Processus:

    id = 0


    @classmethod
    def _generate_id(cls):
        """
        Class method for id generation
        Assigns id then increment for next generation

        Args:
        -----
        None

        Returns:
        --------
        result : `int`
            Processus ID
        """
        result = cls.id
        cls.id +=1
        return result


    def __init__(self, data = dict()) -> None:
        """
        A processus is a sub-part of an application
        A processus is defined as a values corresponding to resource requests
        Initializes the processus values with zeros

        Args:
        -----
        None

        Returns:
        --------
        None
        """

        self.id = Processus._generate_id()

        self.resource_request = dict()
        self.resource_allocation = dict()
        self.app_id = -1

        if data:
            self.initFromDict(data)

        else:
            # A process requests ressources among the 4 resources defined : CPU, GPU, Memory and Disk
            self.resource_request = {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}
            self.resource_allocation = {'cpu' : 0, 'gpu' : 0, 'mem' : 0, 'disk' : 0}
            self.app_id = -1


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


    def setProcessusID(self, id):
        """
        Used to set a processus's ID by hand if necessary

        Args:
        -----
        id : `int`
            New processus ID

        Returns:
        --------
        None
        """
        self.id = id


    def getProcessusID(self):
        """
        Used to get a processus's ID

        Args:
        -----
        None

        Returns:
        --------
        id : `int`
            Processus ID
        """
        return self.id


    def setProcessusResourceRequest(self, resource, resource_request):
        """
        Sets Processus Resource (CPU, GPU, Mem, Disk) Request

        Args:
        -----
        resource : `str`
            Resource name
        resource_request : `float`
            Quantity of a given resource to request from device.
        """
        self.resource_request[resource] = resource_request


    def setAllResourceRequest(self, resources):
        """
        Sets All Processus Resource (CPU, GPU, Mem, Disk) Request

        Removes previous values for safety

        Args:
        -----
        resources : `dict`
            dictionary of all resources to request
        """
        self.resource_request = dict()

        for resource, resource_request in resources.items():
            self.setProcessusResourceRequest(resource, resource_request)


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


    def initFromDict(self, data):

        self.setProcessusID(data["proc_id"])

        self.setAllResourceRequest(data["proc_resource_request"])

        self.resource_allocation = dict()
        for key in self.resource_request:
            self.resource_allocation[key] = 0
