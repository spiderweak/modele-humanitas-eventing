"""
EventQueue Module

This module provides the EventQueue class for managing events in a priority queue.
The events are stored based on their priority (time), and the queue supports adding, 
popping, checking for emptiness, and exporting to JSON.

Classes:
    EventQueue: Manages a priority queue of events.

Usage Example:
    queue = EventQueue(env)
    queue.put(event)
    event = queue.pop()
"""

from queue import PriorityQueue
import json

class EventQueue(object):
    """
    Manages a priority queue of events.

    :param env: The simulation environment or any relevant context for the events.
    :type env: Any
    """
    def __init__(self, env):
        """
        Initializes an EventQueue instance.

        :param env: The simulation environment or any relevant context for the events.
        :type env: Any
        """
        self.__queue = PriorityQueue()
        self.__index = 0
        self.env = env

    def is_empty(self):
        """
        Checks if the queue is empty.

        :return: True if the queue is empty, False otherwise.
        :rtype: bool
        """
        return self.__queue.empty()

    def put(self, event):
        """
        Adds an event to the queue.

        :param event: The event to be added to the queue. It should have a 'time' attribute.
        :type event: Any
        """
        self.__queue.put((event.time, self.__index, event))
        self.__index += 1

    def pop(self):
        """
        Pops an event from the queue based on priority (time).

        :return: The event with the highest priority (earliest time).
        :rtype: Any
        """
        return self.__queue.get()

    def export(self, filename="placement.json"):
        """
        Exports the events in the queue to a JSON file.

        :param filename: The name of the file to export the events to. Default is "placement.json".
        :type filename: str
        """
        json_string = json.dumps(self, default=lambda o: o.__json__(), indent=4)
        with open(filename, 'w') as file:
            file.write(json_string)

    def __json__(self):
        """
        Converts the events in the queue to a JSON serializable format.

        :return: A list of events in JSON serializable format.
        :rtype: list
        """
        json_data = []
        for event in self.__queue.queue:
            json_data.append(event[2].__json__())
        return json_data
