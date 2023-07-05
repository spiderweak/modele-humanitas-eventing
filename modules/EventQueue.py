from queue import PriorityQueue
import json

class EventQueue(object):
    # Why not inherit EventQueue directly from PriorityQueue?
    def __init__(self, env):
        self.__queue = PriorityQueue()

        # How will self.__index be used?
        self.__index = 0

        self.env = env


    # check if the queue is empty
    def is_empty(self):
        return self.__queue.empty()


    # add an element in the queue
    def put(self, event):
        self.__queue.put((event.time, self.__index, event))
        self.__index += 1


    # pop an element based on Priority time
    def pop(self):
        return self.__queue.get()


    def export(self, filename="placement.json"):
        json_string = json.dumps(self, default=lambda o: o.__json__(), indent=4)
        with open(filename, 'w') as file:
            file.write(json_string)

    def __json__(self):
        json_data = []
        for event in self.__queue.queue:
            json_data.append(event[2].__json__())
        return json_data
