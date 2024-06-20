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
    def __init__(self, env):
        """
        Initializes an EventQueue instance.

        Args:
            env: The simulation environment or any relevant context for the events.
        """
        self.__queue = PriorityQueue()
        self.__index = 0
        self.env = env

    def is_empty(self):
        """
        Checks if the queue is empty.

        Returns:
            bool: True if the queue is empty, False otherwise.
        """
        return self.__queue.empty()

    def put(self, event):
        """
        Adds an event to the queue.

        Args:
            event: The event to be added to the queue. It should have a 'time' attribute.
        """
        self.__queue.put((event.time, self.__index, event))
        self.__index += 1

    def pop(self):
        """
        Pops an event from the queue based on priority (time).

        Returns:
            The event with the highest priority (earliest time).
        """
        return self.__queue.get()

    def export(self, filename="placement.json"):
        """
        Exports the events in the queue to a JSON file.

        Args:
            filename (str): The name of the file to export the events to. Default is "placement.json".
        """
        json_string = json.dumps(self, default=lambda o: o.__json__(), indent=4)
        with open(filename, 'w') as file:
            file.write(json_string)

    def __json__(self):
        """
        Converts the events in the queue to a JSON serializable format.

        Returns:
            list: A list of events in JSON serializable format.
        """
        json_data = []
        for event in self.__queue.queue:
            json_data.append(event[2].__json__())
        return json_data
