import random

class Processus:

    id = 0


    @classmethod
    def _generate_id(cls):
        """
        Class method for id generation
        Assigns id then increment for next generation

        Args:
            None

        Returns:
            result : int, Processus ID
        """
        result = cls.id
        cls.id +=1
        return result


    def __init__(self) -> None:
        """
        A processus is a sub-part of an application
        A processus is defined as a values corresponding to resource requests
        Initializes the processus values with zeros

        Args:
            None

        Returns:
            None
        """

        self.id = Processus._generate_id()

        # A process requests ressources among the 4 resources defined : CPU, GPU, Memory and Disk
        self.cpu_request = 0
        self.gpu_request = 0
        self.mem_request = 0 * 1024
        self.disk_request = 0 * 1024

        self.cpu_allocation = 0
        self.gpu_allocation = 0
        self.mem_allocation = 0
        self.disk_allocation = 0

        self.app_id = -1


    def __add__(self, other):

        if isinstance(other, int):
            if other == 0:
                return self

        if isinstance(other, Processus):
            new_proc = Processus()

            new_proc.setProcessusCPURequest(self.cpu_request + other.cpu_request)
            new_proc.setProcessusGPURequest(self.gpu_request + other.gpu_request)
            new_proc.setProcessusMemRequest(self.mem_request + other.mem_request)
            new_proc.setProcessusDiskRequest(self.disk_request + other.disk_request)

            return new_proc
        else:
            raise TypeError


    def __radd__(self, other):
        return self.__add__(other)


    def setProcessusID(self, id):
        """
        Used to set a processus's ID by hand if necessary

        Args:
            id : int, new processus ID

        Returns:
            None
        """
        self.id = id


    def getProcessusID(self):
        """
        Used to get a processus's ID

        Args:
            None

        Returns:
            id : int, processus ID
        """
        return self.id


    def setProcessusCPURequest(self, cpu):
        """
        Sets Processus CPU Request

        Args:
            cpu : float, number of CPUs to request from device.

        Returns:
            None
        """
        self.cpu_request = cpu


    def setProcessusGPURequest(self, gpu):
        """
        Sets Processus GPU Request

        Args:
            gpu : float, number of GPUs to request from device.

        Returns:
            None
        """
        self.gpu_request = gpu


    def setProcessusMemRequest(self, mem):
        """
        Sets Processus Memory Request

        Args:
            mem : float, quantity of memory to request from device, in MBytes.

        Returns:
            None
        """
        self.mem_request = mem


    def setProcessusDiskRequest(self, disk):
        """
        Sets Processus Disk Space Request

        Args:
            disk : float, quantity of disk space to request from device, in MBytes.

        Returns:
            None
        """
        self.disk_request = disk


    def randomProcInit(self):
        """
        Random processus initialization :
            Random number of CPU between 0.5 and 4
            Random number of GPU between 0 and 8
            Random Memory between 0.1 and 4 GigaBytes
            Random Disk space between 10 and 100 GigaBytes

        Args:
            None

        Returns:
            None
        """

        self.setProcessusCPURequest(random.choice([0.5,1,2,3,4]))

        self.setProcessusGPURequest(random.choice([0,0.5,1,4,6,8]))

        self.setProcessusMemRequest((random.random() * 0.975 + 0.025) * 4 * 1024)

        self.setProcessusDiskRequest((random.random() * 9 + 1) * 10 * 1024)


    def processus_yaml_parser(self, processus_yaml):
        """
        Parser to load application characteristics from yaml file, usually called from the app configuration.

        Args:
            processus_yaml : dictionary from yaml file content.

        Returns:
            None
        """
        processus_content = processus_yaml['Processus']

        self.setProcessusCPURequest(processus_content['cpu'])
        self.setProcessusGPURequest(processus_content['gpu'])
        self.setProcessusMemRequest(processus_content['memory'])
        self.setProcessusDiskRequest(processus_content['disk'])