import logging
from modules.resource.Path import Path
from modules.Environment import Environment
from modules.EventQueue import EventQueue
from modules.fullstateprocessing.FullStateProcessing import CeilingUnlimitedMigration
import json

from typing import Any

class Event():
    """An event with event_number occurs at a specific time ``event_time`` and involves a specific
        event type ``event_type``. Comparing two events amounts to figuring out which event occurs first """

    def __init__(self, event_name, queue: EventQueue, event_time=None):

        self.name = event_name
        self.queue = queue
        self.time = event_time
        self.priority = 0

        if event_time is None:
            self.time = queue.env.current_time
        elif event_time < queue.env.current_time:
            self.time = queue.env.current_time


    def __lt__(self, other):
        """ Returns True if self.event_time < other.event_time"""
        return (self.time < other.time) or (self.time == other.time and self.priority < other.priority)


    def add_to_queue(self):
        self.queue.put(self)


    def get_event(self):
        """Gets the first event in the event list"""
        event = self.queue.get()
        return event


    def get_name(self):
        """ returns event name"""
        return self.name

    def get_time(self):
        """ returns event time"""
        return self.time


    def set_time(self, event_time=None):
        self.time = event_time
        if event_time is None:
            self.time = self.queue.env.current_time
        elif event_time < self.queue.env.current_time:
            self.time = self.queue.env.current_time

